from pydantic import BaseModel
from datetime import datetime
from typing import List

class ObservationRequest(BaseModel):
    url: str

class AgentMemoryEntry(BaseModel):
    timestamp: datetime
    observation: str
    plan: str
    result: str