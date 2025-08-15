# app/core/orchestrator.py
from typing import Optional, List, Dict, Any
from app.schemas.report import CallReport
from app.schemas.claim import Claim
from app.schemas.evidence import Evidence
from app.schemas.verdict import Verdict
from app.services.asr import transcribe
from app.agents.claims import extract_claims
from app.agents.retriever import retrieve_evidence_for_claims
from app.agents.verifier import verify
from app.agents.summarizer import make_report
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")


def process_call(audio_path: Optional[str] = None, transcript: Optional[str] = None) -> CallReport:
    print("[orchestrator] START")

    segments = transcribe(audio_path) if audio_path else [
        {"start":0.0,"end":0.0,"speaker":"A","text": transcript or ""}]

    # 2) Claim extraction (IBM)
    claims: List[Claim] = extract_claims(segments)
    print(f"[orchestrator] Claims extracted: {len(claims)}")
    if not claims:
        print("[orchestrator] No claims found; building minimal report.")
        return make_report(segments, [], [], [])

    # 3) Evidence retrieval (IBM embeddings + optional rerank)
    claims, evmap = retrieve_evidence_for_claims(claims, k=8)
    ev_count = sum(len(v) for v in evmap.values())
    evidence_flat = [e for lst in evmap.values() for e in lst]

    verdicts: List[Verdict] = verify(claims, evmap)
    print(f"[orchestrator] Verifier produced {len(verdicts)} verdicts")

    # 5) Summarize
    report = make_report(segments, claims, evidence_flat, verdicts)
    print(report.call_summary)
    print("[orchestrator] DONE")
    return report