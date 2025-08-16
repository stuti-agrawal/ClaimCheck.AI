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
import os, re, json

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")


def _norm_snippet(s: str) -> str:
	return re.sub(r"\s+", " ", (s or "").strip()).lower()


def process_call(audio_path: Optional[str] = None, transcript: Optional[str] = None) -> CallReport:
	print("[orchestrator] START")

	segments = transcribe(audio_path) if audio_path else [
		{"start":0.0,"end":0.0,"speaker":"A","text": transcript or ""}]

	# 2) Claim extraction (IBM)
	claims: List[Claim] = extract_claims(segments)
	print(f"[orchestrator] Claims extracted: {len(claims)}")
	if not claims:
		print("[orchestrator] No claims found; building minimal report.")
		return make_report(segments, [], [], [], evidence_by_claim={})

	# 3) Evidence retrieval (IBM embeddings + optional rerank)
	claims, evmap = retrieve_evidence_for_claims(claims, k=8)
	ev_count = sum(len(v) for v in evmap.values())

	# Print evidence per claim (detailed)
	print("[orchestrator] Evidence per claim (top k):")
	for c in claims:
		evs = evmap.get(c.id, [])
		print(f"  - Claim {c.id}: {c.text}")
		for i, e in enumerate(evs, 1):
			snippet_preview = _norm_snippet(e.snippet)[:200]
			meta_preview = ""
			try:
				meta_preview = json.dumps(e.metadata, ensure_ascii=False)[:160]
			except Exception:
				meta_preview = str(e.metadata)[:160]
			print(f"      {i:02d}. {e.source or e.doc_id}  id={e.doc_id}  score={e.score:.2f}")
			print(f"          {snippet_preview}")
			if e.metadata:
				print(f"          meta: {meta_preview}")

	# Flatten and deduplicate global evidence by normalized snippet, keeping highest score
	flat: List[Evidence] = [e for lst in evmap.values() for e in lst]
	by_snippet: Dict[str, Evidence] = {}
	for e in flat:
		key = _norm_snippet(e.snippet)
		best = by_snippet.get(key)
		if not best or (e.score or 0.0) > (best.score or 0.0):
			by_snippet[key] = e
	evidence_flat = list(by_snippet.values())

	verdicts: List[Verdict] = verify(claims, evmap)
	print(f"[orchestrator] Verifier produced {len(verdicts)} verdicts")
	print("[orchestrator] Verdicts with citations:")
	for v in verdicts:
		cites = getattr(v, "citation_ids", [])
		print(f"  - {v.claim_id}: {v.label}  conf={v.confidence:.2f}  best={v.best_evidence_id}  cites={cites}")

	# 5) Summarize
	report = make_report(segments, claims, evidence_flat, verdicts, evidence_by_claim=evmap)
	print(report.call_summary)
	print("[orchestrator] DONE")
	return report