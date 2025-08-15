# app/agents/verifier.py
from __future__ import annotations
import os, json, requests
from typing import List, Dict

from app.schemas.claim import Claim
from app.schemas.evidence import Evidence
from app.schemas.verdict import Verdict
from app.core.config import WATSONX_BASE_URL, WATSONX_PROJECT, IBM_VERIFIER_MODEL_ID, IBM_API_VERSION
from app.core.auth import get_ibm_iam_token
from app.core.parse_json import parse_json_anywhere 

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

def _gen(url: str, body: dict, timeout: int = 120) -> str:
    """Low-level call to watsonx text/generation; returns raw model text."""
    tok = get_ibm_iam_token()
    headers = {
        "Authorization": f"Bearer {tok}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    r = requests.post(url, headers=headers, json=body, timeout=timeout)
    r.raise_for_status()
    j = r.json()
    res = j.get("results") or []
    return (res[0].get("generated_text") if res else "") or ""

def _post_generation(prompt: str) -> dict:
    """Call model → parse with parse_json_anywhere(root='verdicts') → repair once if needed."""
    url = f"{WATSONX_BASE_URL.rstrip('/')}/ml/v1/text/generation?version={IBM_API_VERSION}"
    body = {
        "input": prompt,
        "model_id": IBM_VERIFIER_MODEL_ID,
        "project_id": WATSONX_PROJECT,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 600,
            "min_new_tokens": 0,
            "repetition_penalty": 1.0,
            "temperature": 0.0,
        },
    }

    text = _gen(url, body)
    parsed = parse_json_anywhere(text, root_key="verdicts")
    if parsed and parsed.get("verdicts"):
        return parsed

    # One-shot repair: coerce to strict JSON with 'verdicts' root
    repair_body = {
        "input": (
            "Return ONLY valid JSON object with root key 'verdicts' "
            "(no prose, no markdown). If invalid, fix and output JSON:\n\n" + text
        ),
        "model_id": IBM_VERIFIER_MODEL_ID,
        "project_id": WATSONX_PROJECT,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 400,
            "temperature": 0.0,
        },
    }
    repaired = _gen(url, repair_body)
    reparsed = parse_json_anywhere(repaired, root_key="verdicts")
    if reparsed and reparsed.get("verdicts"):
        return reparsed

    # Debug preview if still not parsable
    print("[verifier] RAW OUTPUT >>>", (text or repaired)[:1000])
    return {"verdicts": []}

def verify(claims: List[Claim], evidence_map: Dict[str, List[Evidence]]) -> List[Verdict]:
    """
    claims: list of Claim (must have .id and .text)
    evidence_map: claim_id -> List[Evidence] (must have .doc_id, .snippet)
    returns: List[Verdict]
    """
    # 1) Flatten evidence to a doc_id -> snippet catalog
    doc_catalog: Dict[str, str] = {}
    for lst in evidence_map.values():
        for e in lst:
            doc_catalog.setdefault(e.doc_id, e.snippet)

    # 2) Minimal claims JSON for the LLM
    claims_json = [{"id": c.id, "text": c.text} for c in claims]

    # 3) Build prompt
    prompt = (
        PROMPT
        .replace("{CLAIMS_JSON}", json.dumps(claims_json, ensure_ascii=False))
        .replace("{EVIDENCE_JSON}", json.dumps(doc_catalog, ensure_ascii=False))
    )

    # 4) Call model + robust parse
    try:
        parsed = _post_generation(prompt)
    except Exception as e:
        # Fail-safe: mark all as insufficient
        print(f"[verifier] generation failed: {e}")
        return [
            Verdict(
                claim_id=c.id,
                label="insufficient",
                confidence=0.4,
                best_evidence_id="",
                rationale="Verifier offline; defaulting to insufficient."
            )
            for c in claims
        ]

    # 5) Convert to Verdict[]
    allowed = {"supported", "refuted", "insufficient"}
    items = parsed.get("verdicts", []) or []

    # Tiebreaker: top retrieved evidence per claim
    top_ev: Dict[str, str] = {}
    for c in claims:
        evs = evidence_map.get(c.id, [])
        best = max(evs, key=lambda e: e.score, default=None)
        top_ev[c.id] = best.doc_id if best else ""

    out: List[Verdict] = []
    for it in items:
        cid = it.get("claim_id", "")
        label = (it.get("label") or "").lower()
        conf = float(it.get("confidence", 0.5))
        cites = it.get("citation_ids") or []
        rationale = (it.get("rationale") or "")[:300]
        if label not in allowed:
            label = "insufficient"

        # choose best_evidence_id from cited doc_ids or fallback to top_ev
        best_id = next((d for d in cites if d in doc_catalog), "") or top_ev.get(cid, "")

        out.append(Verdict(
            claim_id=cid,
            label=label,
            confidence=conf,
            best_evidence_id=best_id,
            rationale=rationale
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
