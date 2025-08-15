# app/agents/claims.py
from typing import List, Dict
from app.schemas.claim import Claim
from app.agents.ibm_client import run_claim_extractor

def extract_claims(segments: List[Dict]) -> List[Claim]:
    transcript = " ".join(s.get("text","") for s in segments).strip()
    if not transcript:
        return []
    data = run_claim_extractor(transcript)
    items = data.get("claims", [])
    claims: List[Claim] = []
    for i, c in enumerate(items):
        text = (c.get("text") or "").strip()
        if not text:
            continue
        claims.append(Claim(
            id=f"c{i}",
            text=text,
            speaker=c.get("speaker"),
            segment_idx=0,  # map to real segment later using start/end
            confidence=float(c.get("confidence", 0.6))
        ))
    return claims
