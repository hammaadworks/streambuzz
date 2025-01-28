from typing import Optional

from pydantic import BaseModel


class StreamMetadata(BaseModel):
    title: str
    channel_title: str
    thumbnail_url: str


class StreamMetadataDB(StreamMetadata):
    session_id: str
    video_id: str
    live_chat_id: str
    next_chat_page: Optional[str] = ""
    is_active: Optional[int] = 1


class BuzzModel(BaseModel):
    summary: str
    intent: str
    response: str


class StreamBuzzModel(BuzzModel):
    session_id: str
    chat: str
    author: str
    buzz_status: Optional[int] = 0


class WriteChatModel(BaseModel):
    session_id: str
    live_chat_id: str
    retry_count: Optional[int] = 0
    raw_reply: str
    reply_summary: str
    is_written: Optional[int] = 0
