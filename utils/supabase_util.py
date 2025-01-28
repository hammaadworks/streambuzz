from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import HTTPException
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart

from constants.constants import CONVERSATION_CONTEXT, MODEL_RETRIES, SUPABASE_CLIENT
from models.agent_models import ProcessedChunk
from models.youtube_models import StreamBuzzModel, StreamMetadataDB

# Load environment variables
load_dotenv()

# Table names
MESSAGES = "messages"
YT_KEYS = "youtube_keys"
YT_STREAMS = "youtube_streams"
YT_BUZZ = "youtube_buzz"
YT_REPLY = "youtube_reply"
STREAMER_KB = "streamer_knowledge"


# MESSAGES table queries
async def fetch_human_session_history(
        session_id: str, limit: int = 10
) -> list[str]:
    """Fetch the most recent human conversation history for a session."""
    try:
        response = (
            SUPABASE_CLIENT.table(MESSAGES)
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        messages = []
        for msg in response.data:
            if msg["message"]["type"] == "human":
                messages.append(msg["message"]["content"])
        return messages[:CONVERSATION_CONTEXT]
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch_human_session_history: {str(e)}"
        )


async def fetch_conversation_history(
        session_id: str, limit: int = 10
) -> list[ModelRequest | ModelResponse]:
    """Fetch the most recent conversation history for a session."""
    try:
        response = (
            SUPABASE_CLIENT.table(MESSAGES)
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        # Convert to list and reverse to get chronological order
        conversation_history = response.data[::-1]

        # Convert conversation history to format expected by Pydantic AI
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
        SUPABASE_CLIENT.table(MESSAGES).insert(
            {"session_id": session_id, "message": message_obj}
        ).execute()
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to store_message: {str(e)}"
        )


# YT_KEYS table queries
async def get_youtube_api_keys() -> List[Dict[str, Any]]:
    """Fetch the YouTube api keys and access tokens"""
    try:
        response = (
            SUPABASE_CLIENT.table(YT_KEYS).select("api_key, access_token").execute()
        )
        return response.data
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get_youtube_api_keys: {str(e)}"
        )


# YT_STREAMS table queries
async def start_stream(stream_metadata_db: StreamMetadataDB):
    """Store stream details for a given session."""
    try:
        SUPABASE_CLIENT.table(YT_STREAMS).insert(
            {
                "session_id": stream_metadata_db.session_id,
                "video_id": stream_metadata_db.video_id,
                "live_chat_id": stream_metadata_db.live_chat_id,
                "next_chat_page": stream_metadata_db.next_chat_page,
                "is_active": stream_metadata_db.is_active
            }
        ).execute()
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start_stream: {str(e)}")


async def deactivate_existing_streams(session_id: str):
    """
    Update the is_active flag for all streams associated with a given session.

    Args:
        session_id (str): The session ID for which to deactivate streams.

    Raises:
        HTTPException: If there is an error updating the streams.
    """
    try:
        SUPABASE_CLIENT.table(YT_STREAMS).update({"is_active": 0}).eq(
            "session_id", session_id
        ).execute()
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to deactivate_existing_streams: {str(e)}"
        )


async def update_next_chat_page(session_id: str, next_chat_page: str):
    """
    Update the next chat page for a given session.

    Args:
        session_id (str): The session ID for which to update the next chat page.
        next_chat_page (str): The next chat page to update.

    Raises:
        HTTPException: If there is an error updating the next chat page.
    """
    try:
        SUPABASE_CLIENT.table(YT_STREAMS).update({"next_chat_page": next_chat_page}).eq(
            "session_id", session_id
        ).execute()
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update_next_chat_page: {str(e)}"
        )


# YT_BUZZ table queries
async def store_buzz(buzz: StreamBuzzModel):
    """Store a buzz in the Supabase table."""
    try:
        SUPABASE_CLIENT.table(YT_BUZZ).insert(
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
        SUPABASE_CLIENT.table(YT_BUZZ).update({"is_read": 1}).eq(
            "session_id", session_id
        ).execute()
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to read_existing_buzz: {str(e)}"
        )


# YT_REPLY table queries
async def mark_existing_buzz_written(session_id: str):
    """Mark all buzz read for a given session"""
    try:
        SUPABASE_CLIENT.table(YT_REPLY).update({"is_written": 1}).eq(
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
        response = (
            SUPABASE_CLIENT.table(YT_REPLY)
            .select("*")
            .eq("is_written", 0)
            .lt("retry_count", MODEL_RETRIES)
            .execute()
        )
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
        response = (
            SUPABASE_CLIENT.table(YT_REPLY)
            .select("*")
            .eq("is_written", 0)
            .lt("retry_count", MODEL_RETRIES)
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get_unwritten_chats: {str(e)}"
        )


# STREAMER_KB table queries


async def get_previous_kb_file_name(session_id):
    """
    Get the previous knowledge base file name for a given session.

    Args:
        session_id (str): The session ID for which to retrieve the previous knowledge
        base file name.

    Returns:
        str: The previous knowledge base file name.

    Raises:
        HTTPException: If there is an error retrieving the previous knowledge base
        file name.
    """
    try:
        response = (
            SUPABASE_CLIENT.table(STREAMER_KB)
            .select("file_name")
            .eq("session_id", session_id)
            .execute()
        )
        return response.data[0]["file_name"] if response.data else ""
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get_previous_kb_file_name: {str(e)}"
        )


async def delete_previous_kb_entries(session_id):
    """
    Delete the previous knowledge base entries for a given session.

    Args:
        session_id (str): The session ID for which to delete the previous knowledge
        base entries.

    Raises:
        HTTPException: If there is an error deleting the previous knowledge base
        entries.
    """
    try:
        SUPABASE_CLIENT.table(STREAMER_KB).delete().eq(
            "session_id", session_id
        ).execute()
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete_previous_kb_entries: {str(e)}"
        )


async def insert_chunk(chunk: ProcessedChunk):
    """Insert a processed chunk into SUPABASE_CLIENT."""
    try:
        data = {
            "session_id": chunk.session_id,
            "file_name": chunk.file_name,
            "chunk_number": chunk.chunk_number,
            "title": chunk.title,
            "summary": chunk.summary,
            "content": chunk.content,
            "embedding": chunk.embedding,
        }

        result = SUPABASE_CLIENT.table(STREAMER_KB).insert(data).execute()
        print(f"Inserted chunk {chunk.chunk_number} for {chunk.session_id}")
        return result
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to insert_chunk: {chunk=}\n{str(e)}"
        )
