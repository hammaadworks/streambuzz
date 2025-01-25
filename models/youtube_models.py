from typing import Optional

from pydantic import BaseModel

from typing import Optional


class StreamMetadata(BaseModel):
    title: str
    channel_title: str
    thumbnail_url: str


class StreamMetadataDB(StreamMetadata):
    session_id: str
    video_id: str
    live_chat_id: str
    next_chat_page: Optional[str]


class BuzzModel(BaseModel):
    summary: str
    intent: str


class StreamBuzzModel(BuzzModel):
    session_id: str
    chat: str
    author: str
    is_read: Optional[int]

class WriteChatModel(BaseModel):
    session_id: str
    live_chat_id: str
    retry_count: Optional[int]
    raw_reply: str
    reply_summary: str
    is_written: Optional[int]
    