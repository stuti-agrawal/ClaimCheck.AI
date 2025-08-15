# app/agents/ibm_client.py
import os, json, re, requests
from typing import Dict, Any
from app.core.config import WATSONX_BASE_URL, WATSONX_PROJECT
from app.core.ibm_auth import ibm_iam_token  # we wrote this earlier

GEN_URL = f"{WATSONX_BASE_URL}/ml/v1/text/generation?version=2023-05-29"
MODEL_ID = os.getenv("IBM_CLAIM_EXTRACTOR_MODEL", "ibm/granite-3-8b-instruct")

# Few-shot, strict-JSON prompt. We’ll append the runtime transcript at the end.
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

def _build_payload(transcript: str) -> Dict[str, Any]:
    prompt = PROMPT_TEMPLATE.replace("{TRANSCRIPT}", transcript.strip())
    return {
        "input": prompt,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 200,
            "min_new_tokens": 0,
            "repetition_penalty": 1.0,
            # Stop when it tries to start another example
            "stop_sequences": ["\n\nInput:", "\nInput:"]
        },
        "model_id": MODEL_ID,
        "project_id": WATSONX_PROJECT,
        # Keep moderations minimal; you can re-enable if your org requires it
        "moderations": {
            "hap": {"input": {"enabled": False}, "output": {"enabled": False}},
            "pii": {"input": {"enabled": False}, "output": {"enabled": False}}
        }
    }

def _post_generation(payload: Dict[str, Any]) -> str:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ibm_iam_token()}",
    }
    r = requests.post(GEN_URL, headers=headers, json=payload, timeout=90)
    if r.status_code != 200:
        raise RuntimeError(f"watsonx generation error: {r.status_code} {r.text}")
    data = r.json()
    # watsonx usually returns {"results":[{"generated_text":"..."}], ...}
    txt = ""
    if isinstance(data, dict) and "results" in data and data["results"]:
        txt = data["results"][0].get("generated_text", "")
    elif isinstance(data, dict) and "generated_text" in data:
        txt = data["generated_text"]
    return txt.strip()

def _extract_json_block(text: str) -> Dict[str, Any]:
    """
    Try direct JSON parse; if that fails, find the first {...} block and parse it.
    """
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        return {"claims": []}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {"claims": []}

def run_claim_extractor(transcript: str) -> Dict[str, Any]:
    payload = _build_payload(transcript)
    out_text = _post_generation(payload)
    return _extract_json_block(out_text)  # -> {"claims":[...]}
