# app/agents/ibm_client.py
from __future__ import annotations
import os, json, re, time, requests
from typing import Dict, Any, List

from app.core.config import WATSONX_BASE_URL, WATSONX_PROJECT, IBM_CLAIM_MODEL_ID
from app.core.auth import get_ibm_iam_token
from app.schemas.claim import Claim
from app.core.parse_json import parse_json_anywhere

GEN_URL = f"{WATSONX_BASE_URL.rstrip('/')}/ml/v1/text/generation?version=2023-05-29"

def _gen_post(payload: Dict[str, Any], retries: int = 4, timeout: int = 90) -> str:
    """
    POST to watsonx text/generation with basic retries for 429/5xx.
    Returns the text (generated_text/output_text) or raises.
    """
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_ibm_iam_token()}",
    }
    backoff = 1.5
    for attempt in range(retries):
        r = requests.post(GEN_URL, headers=headers, json=payload, timeout=timeout)
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(backoff * (2 ** attempt))
            continue
        r.raise_for_status()
        data = r.json()
        results = data.get("results") or []
        if results and isinstance(results, list):
            return (results[0].get("generated_text") or results[0].get("output_text") or "").strip()
        return (data.get("generated_text") or "").strip()
    # final raise
    r.raise_for_status()
    return ""  # unreachable, keeps linters happy


# =========================
# Claims Extraction (prompt + call)
# =========================

PROMPT_TEMPLATE = r"""
You extract factual claims from messy spoken transcripts.
Return strict JSON with this shape:
{
  "claims": [
    {"text": str, "speaker": str|null, "start": float, "end": float, "confidence": float}
  ]
}

Guidelines:
- A "claim" is a checkable factual assertion (metrics, quantities, time-bound facts).
- Prefer sentences with numbers, percentages, dates, quantities, KPIs.
- Split multiple claims in one sentence into separate objects.
- If unsure about speaker or timestamps, set speaker=null and start/end=0.
- Do NOT include opinions, greetings, or questions unless they state a checkable fact.
- Output ONLY JSON. No prose.

Input: We grew forty percent quarter over quarter in Q2. Customer churn fell to two percent. According to the CRM, Q2 growth was twelve percent. Churn stabilized at four percent in Q2.
Output: {
  "claims": [
    {"text":"We grew 40% quarter over quarter in Q2","speaker":null,"start":0.0,"end":0.0,"confidence":0.55},
    {"text":"Customer churn fell to 2%","speaker":null,"start":0.0,"end":0.0,"confidence":0.55},
    {"text":"Q2 growth was 12%","speaker":null,"start":0.0,"end":0.0,"confidence":0.7},
    {"text":"Churn stabilized at 4% in Q2","speaker":null,"start":0.0,"end":0.0,"confidence":0.7}
  ]
}

Input: We expanded into three new regions this year. Our operating margin improved by five points since Q1.
Output: {
  "claims": [
    {"text":"We expanded into 3 new regions this year","speaker":null,"start":0.0,"end":0.0,"confidence":0.6},
    {"text":"Operating margin improved by 5 percentage points since Q1","speaker":null,"start":0.0,"end":0.0,"confidence":0.7}
  ]
}

Input: {TRANSCRIPT}
Output:
""".strip()

def _build_claims_payload(transcript: str) -> Dict[str, Any]:
    prompt = PROMPT_TEMPLATE.replace("{TRANSCRIPT}", transcript.strip())
    return {
        "input": prompt,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 1000,
            "min_new_tokens": 0,
            "temperature": 0.0,
            "repetition_penalty": 1.0,
            "stop_sequences": ["\n\nInput:", "\nInput:"]
        },
        "model_id": IBM_CLAIM_MODEL_ID,
        "project_id": WATSONX_PROJECT,
        "moderations": {
            "hap": {"input": {"enabled": False}, "output": {"enabled": False}},
            "pii": {"input": {"enabled": False}, "output": {"enabled": False}}
        }
    }

def run_claim_extractor(transcript: str) -> Dict[str, Any]:
    """
    Calls watsonx to turn a transcript into {"claims":[...]} with robust parsing + auto-repair.
    """
    txt = _gen_post(_build_claims_payload(transcript))
    parsed = parse_json_anywhere(txt, root_key="claims")
    if parsed and parsed.get("claims"):
        return parsed

    # One-shot repair prompt (coerce to strict JSON) if the model added prose noise
    repair_payload = {
        "input": f"Return ONLY valid JSON object with key 'claims'. Fix and output JSON:\n\n{txt}",
        "parameters": {"decoding_method": "greedy", "max_new_tokens": 400, "temperature": 0.0},
        "model_id": CLAIM_MODEL_ID,
        "project_id": WATSONX_PROJECT
    }
    repaired = _gen_post(repair_payload)
    parsed2 = parse_json_anywhere(repaired, root_key="claims")
    if parsed2 and parsed2.get("claims"):
        return parsed2

    # Debug preview (short) to help diagnose prompt drift
    print("[claims][RAW OUTPUT]", (txt or repaired)[:600])
    return {"claims": []}


# =========================
# Public: extract_claims (used by orchestrator)
# =========================

def extract_claims(segments: List[Dict]) -> List[Claim]:
    """
    Aggregates segment texts -> calls run_claim_extractor -> returns List[Claim]
    """
    transcript = " ".join(s.get("text", "") for s in segments).strip()
    if not transcript:
        return []

    data = run_claim_extractor(transcript)
    items = (data or {}).get("claims", [])
    out: List[Claim] = []

    for i, c in enumerate(items):
        text = (c.get("text") or "").strip()
        if not text:
            continue
        out.append(Claim(
            id=f"c{i}",
            text=text,
            speaker=c.get("speaker"),
            segment_idx=0,  # TODO: map to true segment via start/end if available
            confidence=float(c.get("confidence", 0.6)),
        ))
    return out
