# app/agents/summarizer.py
from __future__ import annotations
import os, json, requests, re
from typing import List, Dict, Any
from app.schemas.report import CallReport
from app.schemas.claim import Claim
from app.schemas.evidence import Evidence
from app.schemas.verdict import Verdict
from app.core.config import WATSONX_BASE_URL, WATSONX_PROJECT, WATSONX_API_KEY
from app.core.json_utils import extract_json_obj

VERSION = os.getenv("IBM_API_VERSION", "2023-05-29")
MODEL_ID = os.getenv("IBM_SUMMARY_MODEL_ID", "ibm/granite-3-8b-instruct")

def _iam_token() -> str:
    r = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        data={"grant_type":"urn:ibm:params:oauth:grant-type:apikey","apikey":WATSONX_API_KEY},
        headers={"Content-Type":"application/x-www-form-urlencoded"},
        timeout=30
    )
    r.raise_for_status()
    return r.json()["access_token"]

_JSON = re.compile(r"\{[\s\S]*\}\s*$")


# Replace _safe_json with:
def _safe_json(s: str) -> dict:
    return extract_json_obj(s)

# ---- Prompt for structured output ----
PROMPT = """You are a precise meeting summarizer for sales/stakeholder calls.
Given transcript segments, normalized claims, and their verification labels, produce a concise executive summary.

Return STRICT JSON only with:
{
  "call_summary": "string, <= 6 sentences, neutral, factual",
  "action_items": ["string", "..."]            // 1-6 bullets, imperative
}

Guidelines:
- Emphasize mismatches between stated claims and evidence.
- Mention concrete metrics (%, $, dates) when present.
- Avoid fluff and opinions; be concise and factual.

Segments (JSON):
{SEGMENTS_JSON}

Claims (JSON):
{CLAIMS_JSON}

Verdicts (JSON):
{VERDICTS_JSON}

Now return JSON only:
"""

# ---- Public API ----
def make_report(
    segments: List[Dict[str, Any]],
    claims: List[Claim],
    evidence_flat: List[Evidence],
    verdicts: List[Verdict],
) -> CallReport:
    """
    Build a CallReport:
      - call_summary + action_items from IBM LLM
      - claim_table from verdicts (+ best evidence id)
    """
    # ---- Prepare claim_table from verdicts
    # Map claim_id -> claim text
    id2claim = {c.id: c.text for c in claims}
    claim_table: List[Dict[str, Any]] = []
    for v in verdicts:
        claim_text = id2claim.get(v.claim_id, "")
        row = {
            "claim": claim_text,
            "status": v.label.capitalize(),
            "evidence_source": v.best_evidence_id or ""
        }
        claim_table.append(row)

    # ---- Try IBM Granite for summary/action items
    call_summary = ""
    action_items: List[str] = []
    try:
        tok = _iam_token()
        url = f"{WATSONX_BASE_URL.rstrip('/')}/ml/v1/text/generation?version={VERSION}"
        headers = {
            "Authorization": f"Bearer {tok}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        body = {
            "input": PROMPT \
                .replace("{SEGMENTS_JSON}", json.dumps(segments, ensure_ascii=False)) \
                .replace("{CLAIMS_JSON}", json.dumps([{"id": c.id, "text": c.text} for c in claims], ensure_ascii=False)) \
                .replace("{VERDICTS_JSON}", json.dumps([{
                    "claim_id": v.claim_id,
                    "label": v.label,
                    "confidence": v.confidence,
                    "best_evidence_id": v.best_evidence_id,
                    "rationale": v.rationale
                } for v in verdicts], ensure_ascii=False)),
            "model_id": MODEL_ID,
            "project_id": WATSONX_PROJECT,
            "parameters": {
                "decoding_method": "greedy",
                "temperature": 0.0,
                "max_new_tokens": 300,
                "min_new_tokens": 0,
                "repetition_penalty": 1.0
            }
        }
        r = requests.post(url, headers=headers, json=body, timeout=120)
        r.raise_for_status()
        out = r.json()
        gen = (out.get("results") or [{}])[0].get("generated_text", "")
        parsed = _safe_json(gen)
        call_summary = (parsed.get("call_summary") or "").strip()
        action_items = parsed.get("action_items") or []
        if not isinstance(action_items, list):
            action_items = [str(action_items)]
    except Exception as e:
        # Fallback: extract a terse summary from first few segments
        print(f"[summarizer] watsonx generation failed: {e}")
        texts = [s.get("text","") for s in segments if s.get("text")]
        joined = " ".join(texts)[:450].strip()
        call_summary = (joined + "…") if joined else ""
        if not action_items:
            action_items = ["Review claims vs. evidence and confirm metrics in source-of-truth."]

    # ---- Build CallReport dataclass (schema)
    report = CallReport(
        call_summary=call_summary,
        claim_table=claim_table,
        action_items=action_items,
        claims=claims,
        verdicts=verdicts,
        evidence=evidence_flat
    )
    return report
