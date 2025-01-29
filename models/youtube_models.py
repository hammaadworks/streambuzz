from typing import Optional

from pydantic import BaseModel


class StreamMetadata(BaseModel):
    title: Optional[str] = ""
    channel_title: Optional[str] = ""
    thumbnail_url: Optional[str] = ""


class StreamMetadataDB(StreamMetadata):
    session_id: str
    video_id: str
    live_chat_id: str
    next_chat_page: Optional[str] = ""
    is_active: Optional[int] = 1


class BuzzModel(BaseModel):
    buzz_type: str
    generated_response: str


class StreamBuzzModel(BuzzModel):
    session_id: str
    original_chat: str
    author: str
    buzz_status: Optional[int] = 0
    
class StreamBuzzDisplay(BaseModel):
    buzz_type: str
    original_chat: str
    author: str
    generated_response: str


class WriteChatModel(BaseModel):
    session_id: str
    live_chat_id: str
    retry_count: Optional[int] = 0
    reply: str
    reply_summary: Optional[str] = ""
    is_written: Optional[int] = 0
