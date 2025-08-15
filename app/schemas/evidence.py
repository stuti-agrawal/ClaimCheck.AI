from pydantic import BaseModel
from typing import Dict
class Evidence(BaseModel):
    doc_id: str
    source: str
    snippet: str
    score: float
    metadata: Dict[str, str] = {}
