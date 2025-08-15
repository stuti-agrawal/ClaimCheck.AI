from pydantic import BaseModel
from typing import List, Optional
class Claim(BaseModel):
    id: str
    text: str
    speaker: Optional[str] = None
    segment_idx: Optional[int] = None
    entities: List[str] = []
    confidence: float = 0.0
