from typing import Optional

from pydantic import BaseModel


class StreamMetadata(BaseModel):
    """
    Represents metadata associated with a live stream.

    Attributes:
        title (Optional[str]): The title of the live stream. Defaults to an empty string.
        channel_title (Optional[str]): The title of the channel hosting the live stream. Defaults to an empty string.
        thumbnail_url (Optional[str]): URL of the thumbnail image for the live stream. Defaults to an empty string.
    """

    title: Optional[str] = ""
    channel_title: Optional[str] = ""
    thumbnail_url: Optional[str] = ""


class StreamMetadataDB(StreamMetadata):
    """
    Represents stream metadata stored in a database, extending `StreamMetadata`.

    Attributes:
        session_id (str): A unique identifier for the stream session.
        video_id (str): The unique identifier of the video associated with the stream.
        live_chat_id (str): The unique identifier for the live chat associated with the stream.
        next_chat_page (Optional[str]): A token or URL for fetching the next page of chat messages. Defaults to an empty string.
        is_active (Optional[int]): An integer representing whether the stream is currently active. 1 indicates active, 0 indicates inactive. Defaults to 1.
    """

    session_id: str
    video_id: str
    live_chat_id: str
    next_chat_page: Optional[str] = ""
    is_active: Optional[int] = 1


class BuzzModel(BaseModel):
    """
    Represents a buzz, which is a generated response to a user interaction.

    Attributes:
        buzz_type (str): The type or category of the buzz.
        generated_response (str): The generated response text.
    """

    buzz_type: str
    generated_response: str


class StreamBuzzModel(BuzzModel):
    """
    Represents a buzz associated with a specific stream, extending `BuzzModel`.

    Attributes:
        session_id (str): The unique identifier for the stream session.
        original_chat (str): The original chat message that triggered the buzz.
        author (str): The author of the original chat message.
        buzz_status (Optional[int]): An integer representing the status of the buzz. Defaults to 0.
    """

    session_id: str
    original_chat: str
    author: str
    buzz_status: Optional[int] = 0


class StreamBuzzDisplay(BaseModel):
    """
    Represents a buzz for display purposes, containing the original chat, author, and generated response.

    Attributes:
        buzz_type (str): The type or category of the buzz.
        original_chat (str): The original chat message that triggered the buzz.
        author (str): The author of the original chat message.
        generated_response (str): The generated response text.
    """

    buzz_type: str
    original_chat: str
    author: str
    generated_response: str


class WriteChatModel(BaseModel):
    """
    Represents data related to writing a chat message to a live stream.

    Attributes:
        session_id (str): The unique identifier for the stream session.
        live_chat_id (str): The unique identifier for the live chat associated with the stream.
        retry_count (Optional[int]): The number of times the message has been attempted to be written. Defaults to 0.
        reply (str): The text of the reply to be written.
        reply_summary (Optional[str]): An optional summary of the reply. Defaults to an empty string.
        is_written (Optional[int]): An integer representing whether the message has been successfully written. 1 indicates success, 0 indicates failure. Defaults to 0.
    """

    session_id: str
    live_chat_id: str
    retry_count: Optional[int] = 0
    reply: str
    reply_summary: Optional[str] = ""
    is_written: Optional[int] = 0
