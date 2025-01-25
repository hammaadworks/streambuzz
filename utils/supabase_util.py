import os
from typing import Optional, Dict, List, Any

from dotenv import load_dotenv
from fastapi import HTTPException
from pydantic_ai.messages import ModelRequest, UserPromptPart, ModelResponse, TextPart
from supabase import create_client, Client

from constants.constants import MODEL_RETRIES
from models.youtube_models import StreamBuzzModel, StreamMetadataDB

# Load environment variables
load_dotenv()

# Table names
MESSAGES = "messages"
YT_KEYS = "youtube_keys"
YT_STREAMS = "youtube_streams"
YT_BUZZ = "youtube_buzz"
YT_REPLY = "youtube_reply"

# Supabase setup
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY")
)


async def get_youtube_api_keys() -> List[Dict[str, Any]]:
    """Fetch the youtube api keys and access tokens"""
    try:
        response = supabase.table(YT_KEYS).select("api_key, access_token").execute()
        return response.data
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get_youtube_api_keys: {str(e)}"
        )


async def fetch_conversation_history(
        session_id: str, limit: int = 10
) -> List[ModelRequest | ModelResponse]:
    """Fetch the most recent conversation history for a session."""
    try:
        response = (
            supabase.table(MESSAGES)
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        # Convert to list and reverse to get chronological order
        conversation_history = response.data[::-1]

        # Convert conversation history to format expected by agent
        # This will be different depending on your framework (Pydantic AI, LangChain, etc.)
        messages = []
        for msg in conversation_history:
            msg_data = msg["message"]
            msg_type = msg_data["type"]
            msg_content = msg_data["content"]
            msg = (
                ModelRequest(parts=[UserPromptPart(content=msg_content)])
                if msg_type == "human"
                else ModelResponse(parts=[TextPart(content=msg_content)])
            )
            messages.append(msg)
        return messages
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch_conversation_history: {str(e)}"
        )


async def store_message(
        session_id: str, message_type: str, content: str, data: Optional[Dict] = None
):
    """Store a message in the Supabase messages table."""
    message_obj = {"type": message_type, "content": content}
    if data:
        message_obj["data"] = data

    try:
        supabase.table(MESSAGES).insert(
            {"session_id": session_id, "message": message_obj}
        ).execute()
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to store_message: {str(e)}"
        )


async def deactivate_existing_streams(session_id: str):
    """
    Update the is_active flag for all streams associated with a given session.

    Args:
        session_id (str): The session ID for which to deactivate streams.

    Raises:
        HTTPException: If there is an error updating the streams.
    """
    try:
        supabase.table(YT_STREAMS).update({"is_active": 0}).eq(
            "session_id", session_id
        ).execute()
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to deactivate_existing_streams: {str(e)}"
        )


async def start_stream(stream_metadata_db: StreamMetadataDB):
    """Store stream details for a given session."""
    try:
        supabase.table(YT_STREAMS).insert(
            {
                "session_id": stream_metadata_db.session_id,
                "video_id": stream_metadata_db.video_id,
                "live_chat_id": stream_metadata_db.live_chat_id,
                "next_chat_page": stream_metadata_db.next_chat_page,
            }
        ).execute()
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start_stream: {str(e)}")


async def store_buzz(buzz: StreamBuzzModel):
    """Store a buzz in the Supabase table."""
    try:
        supabase.table(YT_BUZZ).insert(
            {
                "summary": buzz.summary,
                "intent": buzz.intent,
                "session_id": buzz.session_id,
                "chat": buzz.chat,
                "author": f"@{buzz.author}",
                "is_read": 0,
            }
        ).execute()
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to store_buzz: {str(e)}")


async def mark_existing_buzz_read(session_id: str):
    """Mark all buzz read for a given session"""
    try:
        supabase.table(YT_BUZZ).update({"is_read": 1}).eq(
            "session_id", session_id
        ).execute()
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to read_existing_buzz: {str(e)}"
        )


async def mark_existing_buzz_written(session_id: str):
    """Mark all buzz read for a given session"""
    try:
        supabase.table(YT_REPLY).update({"is_written": 1}).eq(
            "session_id", session_id
        ).execute()
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to read_existing_buzz: {str(e)}"
        )


def get_unwritten_chats():
    """
    Retrieve unwritten chats from the database.

    Returns:
        list: A list of unwritten chats.

    Raises:
        HTTPException: If there is an error retrieving the chats.
    """
    try:
        response = supabase.table(YT_REPLY).select("*").eq("is_written", 0).lt("retry_count", MODEL_RETRIES).execute()
        return response.data
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get_unwritten_chats: {str(e)}"
        )

def live_chat_id_increment_retry(live_chat_id: str):
    """
    Increment the retry count for a given live chat ID.

    Args:
        live_chat_id (str): The live chat ID for which to increment the retry count.

    Returns:
        list: The updated data for the live chat ID.

    Raises:
        HTTPException: If there is an error updating the retry count.
    """
    try:
        response = supabase.table(YT_REPLY).select("*").eq("is_written", 0).lt("retry_count", MODEL_RETRIES).execute()
        return response.data
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get_unwritten_chats: {str(e)}"
        )