from pydantic import BaseModel
from typing import List, Dict
from .claim import Claim
from .evidence import Evidence
from .verdict import Verdict

class CallReport(BaseModel):
	call_summary: str
	claim_table: List[dict]
	action_items: List[str] = []
	claims: List[Claim]
	verdicts: List[Verdict]
	evidence: List[Evidence]
	evidence_by_claim: Dict[str, List[Evidence]] = {}
