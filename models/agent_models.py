# Request/Response Models
from dataclasses import dataclass
from pydantic import BaseModel




class AgentRequest(BaseModel):
    query: str
    user_id: str
    request_id: str
    session_id: str


class AgentResponse(BaseModel):
    success: bool
