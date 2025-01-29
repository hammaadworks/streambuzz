from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import HTTPException
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart

from constants.constants import CONVERSATION_CONTEXT, MODEL_RETRIES, SUPABASE_CLIENT, MESSAGES, YT_KEYS, YT_STREAMS, YT_BUZZ, YT_REPLY, STREAMER_KB
from constants.enums import BuzzStatusEnum, StateEnum
from models.agent_models import ProcessedChunk
from models.youtube_models import StreamBuzzModel, StreamMetadataDB, WriteChatModel

# Load environment variables
load_dotenv()


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
async def get_active_stream(session_id: str) -> StreamMetadataDB:
    """
    Get the active stream for a given session.

    Args:
        session_id (str): The session ID for which to retrieve the active stream.

    Returns:
        dict: The active stream for the given session.

    Raises:
        HTTPException: If there is an error retrieving the active stream.
    """
    try:
        response = (
            SUPABASE_CLIENT.table(YT_STREAMS)
            .select("*")
            .eq("session_id", session_id)
            .eq("is_active", StateEnum.YES.value)
            .execute()
        )
        active_stream = response.data[0]
        return StreamMetadataDB(
            session_id=active_stream["session_id"],
            video_id=active_stream["video_id"],
            live_chat_id=active_stream["live_chat_id"],
            next_chat_page=active_stream["next_chat_page"],
            is_active=active_stream["is_active"]
        ) if active_stream else None
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get_active_stream: {str(e)}"
        )


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
        SUPABASE_CLIENT.table(YT_STREAMS).update({"is_active": StateEnum.NO.value}).eq(
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
        ).eq("is_active", StateEnum.YES.value).execute()
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
                "buzz_type": buzz.buzz_type,
                "session_id": buzz.session_id,
                "chat": buzz.original_chat,
                "author": f"@{buzz.author}",
                "is_read": 0,
            }
        ).execute()
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to store_buzz: {str(e)}")


async def get_current_buzz(session_id: str):
    """
    Get the current buzz for a given session.

    Args:
        session_id (str): The session ID for which to retrieve the current buzz.

    Returns:
        list: The current buzz for the given session.

    Raises:
        HTTPException: If there is an error retrieving the current buzz.
    """
    try:
        response = (
            SUPABASE_CLIENT.table(YT_BUZZ)
            .select("buzz_type, original_chat, author, generated_response")
            .eq("session_id", session_id)
            .eq("buzz_status", BuzzStatusEnum.ACTIVE.value)
            .order("created_at", desc=True)
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        return response.data[0]
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get_current_buzz: {str(e)}"
        )


async def mark_current_buzz_inactive(session_id: str):
    """
    Mark the current buzz for a given session to inactive.

    Args:
        session_id (str): The session ID for which to update the current buzz.

    Raises:
        HTTPException: If there is an error updating the current buzz.
    """
    try:
        response = (
            SUPABASE_CLIENT.table(YT_BUZZ)
            .select("id")
            .eq("session_id", session_id)
            .eq("buzz_status", BuzzStatusEnum.ACTIVE.value)
            .order("created_at", desc=True)
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        if response.data:
            SUPABASE_CLIENT.table(YT_BUZZ).update(
                {"buzz_status": BuzzStatusEnum.INACTIVE.value}
            ).eq(
                "id", response.data[0]["id"]
            ).execute()
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update_current_buzz_inactive: {str(e)}"
        )

async def get_found_buzz():
    """
    Get all found buzz.

    Returns:
        list: The found buzz.

    Raises:
        HTTPException: If there is an error retrieving the found buzz.
    """
    try:
        response = (
            SUPABASE_CLIENT.table(YT_BUZZ)
            .select("id, buzz_type, original_chat")
            .eq("buzz_status", BuzzStatusEnum.FOUND.value)
            .order("created_at")
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get_found_buzz: {str(e)}"
        )


async def update_buzz_status_by_id(id, buzz_status):
    """
    Update the status of a buzz.

    Args:
        id (int): The ID of the buzz to update.
        buzz_status (str): The status to update the buzz to.

    Raises:
        HTTPException: If there is an error updating the buzz status.
    """
    try:
        SUPABASE_CLIENT.table(YT_BUZZ).update(
            {"buzz_status": buzz_status}
        ).eq(
            "id", id
        ).execute()
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update_buzz_status: {str(e)}"
        )



async def update_buzz_status_by_session_id(session_id: str, buzz_status: int):
    """Mark all buzz read for a given session"""
    try:
        SUPABASE_CLIENT.table(YT_BUZZ).update(
            {"buzz_status": buzz_status}
        ).eq(
            "session_id", session_id
        ).execute()
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to read_existing_buzz: {str(e)}"
        )
async def update_buzz_status_batch_by_id(id_list:list[int], buzz_status: int):
    """
    Update the status of a list of buzz.

    Args:
        id_list (list): The list of IDs of the buzz to update.
        buzz_status (str): The status to update the buzz to.

    Raises:
        HTTPException: If there is an error updating the buzz status.
    """
    try:
        SUPABASE_CLIENT.table(YT_BUZZ).update(
            {"buzz_status": buzz_status}
        ).in_(
            "id", id_list
        ).execute()
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update_buzz_status: {str(e)}"
        )


def update_buzz_response_by_id(id:int, generated_response:str):
    """
    Update the response of a buzz.

    Args:
        id (int): The ID of the buzz to update.
        generated_response (str): The generated response to update the buzz with.

    Raises:
        HTTPException: If there is an error updating the buzz response.
    """
    try:
        SUPABASE_CLIENT.table(YT_BUZZ).update(
            {"buzz_status": BuzzStatusEnum.ACTIVE.value, "generated_response": generated_response}
        ).eq(
            "id", id
        ).execute()
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update_buzz_response: {str(e)}"
        )

# YT_REPLY table queries
async def store_reply(reply: WriteChatModel):
    """Store a reply in the Supabase table."""
    try:
        SUPABASE_CLIENT.table(YT_REPLY).insert(
            {
                "session_id": reply.session_id,
                "live_chat_id": reply.live_chat_id,
                "retry_count": reply.retry_count,
                "reply": reply.reply,
                "is_written": StateEnum.NO.value,
            }
        ).execute()
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to store_reply: {str(e)}")


def get_unwritten_replies():
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
            .eq("is_written", StateEnum.NO.value)
            .lt("retry_count", MODEL_RETRIES)
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get_unwritten_chats: {str(e)}"
        )


async def mark_replies_pending(session_id: str):
    """Mark replies as pending before attempting to write for a given session"""
    try:
        SUPABASE_CLIENT.table(YT_REPLY).update(
            {"is_written": StateEnum.PENDING.value}
            ).eq(
            "session_id", session_id
        ).eq(
            "is_written", StateEnum.NO.value
        ).execute()
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to read_existing_buzz: {str(e)}"
        )


async def mark_replies_success(session_id: str):
    """Mark replies as success after writing for a given session"""
    try:
        SUPABASE_CLIENT.table(YT_REPLY).update({"is_written": StateEnum.YES.value}).eq(
            "session_id", session_id
        ).eq(
            "is_written", StateEnum.PENDING.value
        ).execute()
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to read_existing_buzz: {str(e)}"
        )


async def mark_replies_failed(session_id: str):
    """Mark replies as failed after writing for a given session by 
    1. incrementing retry count
    2. updating status to NO"""
    try:
        SUPABASE_CLIENT.table(YT_REPLY).update(
            {
                "is_written": StateEnum.NO.value,
                "retry_count": {"increment": 1}
            }
        ).eq(
            "session_id", session_id
        ).eq(
            "is_written", StateEnum.PENDING.value
        ).execute()
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to read_existing_buzz: {str(e)}"
        )


async def deactivate_replies(session_id: str):
    """Mark all buzz read for a given session"""
    try:
        SUPABASE_CLIENT.table(YT_REPLY).update({"is_written": StateEnum.YES.value}).eq(
            "session_id", session_id
        ).execute()
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to read_existing_buzz: {str(e)}"
        )


# STREAMER_KB table queries
async def get_kb_file_name(session_id):
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
        return response.data[0]["file_name"] if response.data else None
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


async def get_matching_chunks(query_embedding, session_id):
    """
    Get matching chunks for a given query embedding.

    Args:
        query_embedding (list): The query embedding for which to retrieve matching
        chunks.
        session_id (str): The session ID for which to retrieve matching chunks.

    Returns:
        list: The matching chunks for the given query embedding.

    Raises:
        HTTPException: If there is an error retrieving the matching chunks.
    """
    try:
        response = SUPABASE_CLIENT.rpc(
            'match_streamer_knowledge',
            {
                'query_embedding': query_embedding,
                'user_session_id': session_id,
                'match_count': CONVERSATION_CONTEXT,
            }
        ).execute()
        
        return response.data
    except Exception as e:
        print(f"Error>> Failed at supabase_util: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get_matching_chunks: {str(e)}"
        )


