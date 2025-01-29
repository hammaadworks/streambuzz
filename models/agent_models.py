# Request/Response Models
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


@dataclass
class ProcessedChunk:
    session_id: str
    file_name: str
    chunk_number: int
    title: str
    summary: str
    content: str
    embedding: List[float]
    
@dataclass
class ProcessFoundBuzz:
    id: int
    buzz_type: str
    original_chat: str


class AgentRequest(BaseModel):
    query: str
    user_id: str
    request_id: str
    session_id: str
    files: Optional[List[Dict[str, Any]]] = None


class AgentResponse(BaseModel):
    success: bool
