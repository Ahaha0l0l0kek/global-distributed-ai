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

class TaskResponse(BaseModel):
    task_id: str
    agent_id: str
    task: str
    status: str
    result: Optional[str]
    created_at: datetime
    updated_at: datetime
    reply_host: Optional[str]
    reply_port: Optional[int]