# Request/Response Models
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


@dataclass
class ProcessedChunk:
    """
    Represents a processed chunk of a document.

    Attributes:
        session_id (str): The ID of the session this chunk belongs to.
        file_name (str): The name of the file the chunk originates from.
        chunk_number (int): The sequential number of the chunk within the file.
        title (str): The title of the chunk.
        summary (str): A summary of the chunk's content.
        content (str): The actual text content of the chunk.
        embedding (List[float]): A numerical representation (embedding) of the chunk's content.
    """

    session_id: str
    file_name: str
    chunk_number: int
    title: str
    summary: str
    content: str
    embedding: List[float]


@dataclass
class ProcessFoundBuzz:
    """
    Represents a buzz (a specific piece of information or finding) identified during processing.

    Attributes:
        id (int): A unique identifier for the buzz.
        buzz_type (str): The type or category of the buzz.
        original_chat (str): The original text where the buzz was identified.
    """

    id: int
    buzz_type: str
    original_chat: str


class AgentRequest(BaseModel):
    """
    Represents a request sent to an agent.

    Attributes:
        query (str): The user's query or request.
        user_id (str): The ID of the user making the request.
        request_id (str): A unique ID for this specific request.
        session_id (str): The ID of the current session.
        files (Optional[List[Dict[str, Any]]], optional): An optional list of file metadata associated with the request.
            Each dictionary within the list represents a file. Defaults to None.
    """

    query: str
    user_id: str
    request_id: str
    session_id: str
    files: Optional[List[Dict[str, Any]]] = None


class AgentResponse(BaseModel):
    """
    Represents a response from an agent.

    Attributes:
        success (bool): A boolean indicating whether the request was processed successfully.
    """

    success: bool
