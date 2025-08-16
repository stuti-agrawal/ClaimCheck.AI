# app/agents/summarizer.py
from __future__ import annotations
import os, json, time, requests
from typing import List, Dict, Any

from app.schemas.report import CallReport
from app.schemas.claim import Claim
from app.schemas.evidence import Evidence
from app.schemas.verdict import Verdict
from app.core.config import (
    WATSONX_BASE_URL,
    WATSONX_PROJECT,
    IBM_SUMMARY_MODEL_ID as MODEL_ID,
    IBM_API_VERSION,
)
from app.core.auth import get_ibm_iam_token
from app.core.parse_json import parse_json_anywhere


# -------- Helpers --------

def _compact_segments(segments: List[Dict[str, Any]], max_chars: int = 6000) -> List[Dict[str, Any]]:
    """
    Keep the last ~N characters of transcript text to stay under token limits,
    preserving structure (start, end, speaker, text).
    """
    if not segments:
        return []
    # Prefer the tail of the conversation (most recent context is more salient)
    out = []
    total = 0
    for seg in reversed(segments):
        t = seg.get("text", "") or ""
        total += len(t)
        out.append({"start": seg.get("start", 0.0),
                    "end": seg.get("end", 0.0),
                    "speaker": seg.get("speaker"),
                    "text": t})
        if total >= max_chars:
            break
    return list(reversed(out))

def _verdict_stats(verdicts: List[Verdict]) -> Dict[str, int]:
    s = sum(1 for v in verdicts if v.label == "supported")
    r = sum(1 for v in verdicts if v.label == "refuted")
    i = sum(1 for v in verdicts if v.label == "insufficient")
    return {"supported": s, "refuted": r, "insufficient": i, "total": len(verdicts)}

def _http_post_with_retry(url: str, headers: dict, body: dict, timeout: int = 120, tries: int = 4, backoff: float = 1.5):
    for attempt in range(tries):
        r = requests.post(url, headers=headers, json=body, timeout=timeout)
        if r.status_code not in (429, 500, 502, 503, 504):
            r.raise_for_status()
            return r
        time.sleep(backoff * (2 ** attempt))
    # last try result:
    r.raise_for_status()
    return r


# -------- Prompt (kept tight & structured) --------

PROMPT = """You are a precise meeting summarizer for sales/stakeholder calls.
Given transcript segments, normalized claims, and their verification labels, produce a concise executive summary.

Return STRICT JSON only with:
{
  "call_summary": "string (<= 6 sentences, neutral, factual, cites concrete numbers/dates/KPIs when present)",
  "action_items": ["string", "..."]  // 1-6 imperative bullets; each starts with a verb
}

Guidance:
- Emphasize mismatches between stated claims and evidence.
- Prioritize concrete, verifiable metrics (%, $, dates, counts).
- Be concise; avoid fluff and opinions.

Context stats (for your awareness; do not invent numbers):
{VERDICT_STATS}

Segments (JSON):
{SEGMENTS_JSON}

Claims (JSON):
{CLAIMS_JSON}

Verdicts (JSON):
{VERDICTS_JSON}

Output JSON only (no extra text, no markdown, no backticks):
"""


# -------- Public API --------

def make_report(
    segments: List[Dict[str, Any]],
    claims: List[Claim],
    evidence_flat: List[Evidence],
    verdicts: List[Verdict],
    *,
    evidence_by_claim: Dict[str, List[Evidence]] | None = None,
) -> CallReport:
    """
    Build a CallReport:
      - call_summary + action_items from IBM LLM (robust parse)
      - claim_table derived from verdicts (+ best evidence id)
    """

    # 1) Build claim table from verdicts (always succeeds)
    id2claim = {c.id: c.text for c in claims}
    claim_table: List[Dict[str, Any]] = []
    for v in verdicts:
        claim_text = id2claim.get(v.claim_id, "")
        claim_table.append({
            "claim": claim_text,
            "status": v.label.capitalize(),
            "evidence_source": v.best_evidence_id or ""
        })

    # 2) Short-circuit if we have no content to summarize
    if not segments and not claims:
        return CallReport(
            call_summary="",
            claim_table=claim_table,
            action_items=["Review claims vs. evidence and confirm metrics in source-of-truth."],
            claims=claims,
            verdicts=verdicts,
            evidence=evidence_flat,
            evidence_by_claim=evidence_by_claim or {},
        )

    # 3) Prepare compact context + stats
    compact = _compact_segments(segments, max_chars=6000)
    stats = _verdict_stats(verdicts)

    # 4) Call IBM Granite (watsonx) for structured summary
    call_summary = ""
    action_items: List[str] = []

    try:
        tok = get_ibm_iam_token()
        url = f"{WATSONX_BASE_URL.rstrip('/')}/ml/v1/text/generation?version={IBM_API_VERSION}"
        headers = {
            "Authorization": f"Bearer {tok}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        body = {
            "input": PROMPT \
                .replace("{VERDICT_STATS}", json.dumps(stats, ensure_ascii=False)) \
                .replace("{SEGMENTS_JSON}", json.dumps(compact, ensure_ascii=False)) \
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
                "max_new_tokens": 400,
                "min_new_tokens": 0,
                "repetition_penalty": 1.0,
                "stop_sequences": ["\n\n", "\nOutput JSON", "\nSegments (JSON):"]
            }
        }

        resp = _http_post_with_retry(url, headers, body, timeout=120)
        out = resp.json()
        gen = (out.get("results") or [{}])[0].get("generated_text", "") or ""

        # Robust parse (accepts full JSON, partials, or multiple JSON objects)
        parsed = parse_json_anywhere(gen, root_key=None)  # expecting a single dict with keys above
        if isinstance(parsed, dict):
            call_summary = (parsed.get("call_summary") or "").strip()
            action_items = parsed.get("action_items") or []
        else:
            # If parse returns a list (rare), try first dict
            if parsed and isinstance(parsed, list) and isinstance(parsed[0], dict):
                call_summary = (parsed[0].get("call_summary") or "").strip()
                action_items = parsed[0].get("action_items") or []

        if not isinstance(action_items, list):
            action_items = [str(action_items)]

    except Exception as e:
        # 5) Fallback: build a terse summary from first few segments and stats
        print(f"[summarizer] watsonx generation failed: {e}")
        texts = [s.get("text","") for s in compact if s.get("text")]
        joined = " ".join(texts)[:450].strip()
        call_summary = (joined + "…") if joined else ""

    # 6) Return CallReport
    return CallReport(
        call_summary=call_summary,
        claim_table=claim_table,
        action_items=action_items,
        claims=claims,
        verdicts=verdicts,
        evidence=evidence_flat,
        evidence_by_claim=evidence_by_claim or {},
    )
