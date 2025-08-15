# app/agents/verifier.py
from __future__ import annotations
import os, json, re, requests
from typing import List, Dict
from app.schemas.claim import Claim
from app.schemas.evidence import Evidence
from app.schemas.verdict import Verdict
from app.core.config import WATSONX_BASE_URL, WATSONX_PROJECT, WATSONX_API_KEY
from app.core.json_utils import extract_json_obj


VERSION = os.getenv("IBM_API_VERSION", "2023-05-29")
MODEL_ID = os.getenv("IBM_VERIFIER_MODEL_ID", "ibm/granite-3-8b-instruct")
# ---- IAM helper ----
def _iam_token() -> str:
    r = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": WATSONX_API_KEY,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


# Strengthen the prompt header:
PROMPT = """You are a precise fact verifier.
Return STRICT JSON ONLY. Your first character MUST be '{' and your last character MUST be '}'.
Schema:
{
  "verdicts": [
    {"claim_id": "string", "label": "supported|refuted|insufficient", "confidence": 0.0, "citation_ids": ["doc_id", "..."], "rationale": "string"}
  ]
}
# No extra text, no markdown, no backticks.

Rules:
- "supported" if at least one evidence snippet directly supports the claim.
- "refuted" if any evidence directly contradicts the claim.
- "insufficient" if evidence is not enough to decide.
- Cite relevant evidence doc_ids in "citation_ids".
- Keep "rationale" ≤ 2 sentences.

Claims (JSON):
{CLAIMS_JSON}

Evidence catalog (doc_id -> snippet) as JSON:
{EVIDENCE_JSON}

Output JSON:
"""

# Replace _safe_json with:
def _safe_json(s: str) -> dict:
    return extract_json_obj(s)

# In _post_generation() keep as-is, but add debug preview if parse fails:
def _post_generation(prompt: str) -> dict:
    url = f"{WATSONX_BASE_URL.rstrip('/')}/ml/v1/text/generation?version={VERSION}"
    tok = _iam_token()
    headers = {
        "Authorization": f"Bearer {tok}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    body = {
        "input": prompt,
        "model_id": MODEL_ID,
        "project_id": WATSONX_PROJECT,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 400,
            "min_new_tokens": 0,
            "repetition_penalty": 1.0,
            "temperature": 0.0,
        },
    }
    r = requests.post(url, headers=headers, json=body, timeout=120)
    r.raise_for_status()
    out = r.json()
    results = out.get("results") or []
    text = (results[0] or {}).get("generated_text", "") if results else ""
    if not text:
        raise RuntimeError(f"Empty generation response: {out}")
    try:
        return _safe_json(text)
    except Exception as e:
        print("[verifier] RAW OUTPUT >>>", text[:1000])
        raise


def verify(claims: List[Claim], evidence_map: Dict[str, List[Evidence]]) -> List[Verdict]:
    """
    claims: list of Claim (must have .id and .text)
    evidence_map: claim_id -> List[Evidence] (must have .doc_id, .snippet)
    returns: List[Verdict]
    """
    # 1) Flatten evidence to a doc_id -> snippet map (only those we surfaced)
    doc_catalog: Dict[str, str] = {}
    for lst in evidence_map.values():
        for e in lst:
            # Don't overwrite if duplicate doc_ids appear across claims
            doc_catalog.setdefault(e.doc_id, e.snippet)

    # 2) Minimal claims JSON for the LLM
    claims_json = [{"id": c.id, "text": c.text} for c in claims]

    # 3) Render prompt
    prompt = PROMPT.replace("{CLAIMS_JSON}", json.dumps(claims_json, ensure_ascii=False)) \
                   .replace("{EVIDENCE_JSON}", json.dumps(doc_catalog, ensure_ascii=False))

    # 4) Call watsonx
    try:
        parsed = _post_generation(prompt)
    except Exception as e:
        # Fallback: everything "insufficient"
        print(f"[verifier] generation failed: {e}")
        return [
            Verdict(
                claim_id=c.id,
                label="insufficient",
                confidence=0.4,
                best_evidence_id="",
                rationale="Verifier offline; defaulting to insufficient."
            ) for c in claims
        ]

    # 5) Validate + convert to Verdict[]
    out: List[Verdict] = []
    allowed = {"supported", "refuted", "insufficient"}
    items = parsed.get("verdicts", [])
    # Build a quick lookup of top evidence per claim (by retriever score) as tiebreaker
    top_ev: Dict[str, str] = {}
    for c in claims:
        evs = evidence_map.get(c.id, [])
        best = max(evs, key=lambda e: e.score, default=None)
        top_ev[c.id] = best.doc_id if best else ""

    for it in items:
        cid = it.get("claim_id", "")
        label = (it.get("label") or "").lower()
        conf = float(it.get("confidence", 0.5))
        cites = it.get("citation_ids") or []
        rationale = it.get("rationale") or ""

        if label not in allowed:
            label = "insufficient"

        # Choose best_evidence_id:
        best_id = ""
        for d in cites:
            if d in doc_catalog:
                best_id = d
                break
        if not best_id:
            best_id = top_ev.get(cid, "")

        out.append(Verdict(
            claim_id=cid,
            label=label,
            confidence=conf,
            best_evidence_id=best_id,
            rationale=rationale[:300]
        ))

    # Ensure every claim has a verdict
    have = {v.claim_id for v in out}
    for c in claims:
        if c.id not in have:
            out.append(Verdict(
                claim_id=c.id,
                label="insufficient",
                confidence=0.4,
                best_evidence_id=top_ev.get(c.id, ""),
                rationale="No explicit verdict returned; marking as insufficient."
            ))
    return out
