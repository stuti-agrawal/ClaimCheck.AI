from pydantic import BaseModel
class Verdict(BaseModel):
    claim_id: str
    label: str           # supported | refuted | insufficient
    confidence: float
    best_evidence_id: str
    rationale: str
