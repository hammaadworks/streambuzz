from collections import defaultdict
import json
from agents import chat_analyst_agent, orchestrator_agent
from constants.constants import YOUTUBE_LIVE_API_ENDPOINT
from constants.enums import ChatIntentEnum
from constants.prompts import REPLY_SUMMARISER_PROMPT
from models.youtube_models import StreamBuzzModel, WriteChatModel
from utils import supabase_util, youtube_util
from typing import List, Dict, Any
from fastapi import APIRouter

from utils.youtube_util import get_youtube_api_keys
from utils.supabase_util import store_message, mark_existing_buzz_written

# Create API router for managing live chats
router = APIRouter()


def read_live_chats():
    pass


async def group_chats_by_session_id(
    unwritten_chats: List[Dict[str, Any]]
) -> List[WriteChatModel]:
    """
    Group unwritten chats by session ID, live chat ID, and retry count.

    Args:
        unwritten_chats (List[Dict[str, Any]]): The list of unwritten chats.

    Returns:
        List[WriteChatModel]: The grouped chat models.

    Raises:
        Exception: If there is an error during the process.
    """
    try:
        # Prepare the desired output
        grouped_chats = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        # Group chats by session_id, live_chat_id, and retry_count
        for row in unwritten_chats:
            grouped_chats[row["session_id"]][row["live_chat_id"]][
                row["retry_count"]
            ].append(row["reply"])

        # Populate WriteChatModel instances
        result: List[WriteChatModel] = []
        for session_id, live_chat_groups in grouped_chats.items():
            for live_chat_id, retry_groups in live_chat_groups.items():
                for retry_count, chats in retry_groups.items():
                    raw_reply = ". ".join(chats)
                    reply_summary = await orchestrator_agent.run(
                        REPLY_SUMMARISER_PROMPT.format(raw_reply=raw_reply)
                    )
                    result.append(
                        WriteChatModel(
                            session_id=session_id,
                            live_chat_id=live_chat_id,
                            retry_count=retry_count,
                            raw_reply=raw_reply,
                            reply_summary=reply_summary,
                        )
                    )
        return result
    except Exception as e:
        print(f"Error>> group_chats_by_session_id: {str(e)}")
        raise





async def write_live_chats():
    """
    Write live chats to YouTube and update their status in the database.

    Raises:
        Exception: If there is an error during the process.
    """
    try:
        # Get unwritten chats from write_buzz table
        unwritten_chats_query_response = await supabase_util.get_unwritten_chats()
        if not unwritten_chats_query_response:
            return
        grouped_chats: List[WriteChatModel] = await group_chats_by_session_id(
            unwritten_chats_query_response
        )

        # Call insert youtube api on max retries in loop for each of the sessions
        for reply in grouped_chats:
            try:
                params = {"part": "snippet"}
                payload = json.dumps(
                    {
                        "snippet": {
                            "liveChatId": f"{reply.live_chat_id}",
                            "type": "textMessageEvent",
                            "textMessageDetails": {
                                "messageText": f"{reply.reply_summary}"
                            },
                        }
                    }
                )
                await youtube_util.post_request_with_retries(
                    url=YOUTUBE_LIVE_API_ENDPOINT, params=params, payload=payload, api_keys=get_youtube_api_keys()
                )
                await mark_existing_buzz_written(reply.session_id)
                await store_message(
                    session_id=reply.session_id,
                    message_type="ai",
                    content=f"StreamBuzz Bot: I've replied this on live chat\n{reply.reply_summary}",
                    data={"reply_dump": reply.model_dump()},
                )
            except Exception as e:
                print(f"Error>> write_live_chats: {reply.session_id}\n{str(e)}")
                raise
        # if success = update status to written session_id and live_chat_id. Respond that replies have been posted to the DB messages
        # if stream_inactive = deactivate
        # if failed = get retry count; if retry count = 3: deactivate or retry count = +1
    except Exception as e:
        print(f"Error>> write_live_chats: {str(e)}")
        raise


async def process_chat(chat: StreamBuzzModel) -> None:
    """
    Analyze the chat and store the buzz in the database.

    Args:
        chat (StreamBuzzModel): The chat model to process.

    Raises:
        Exception: If there is an error during the process.
    """
    # Analyses the chats and stores the buzz to DB
    try:
        # Process chat and generate buzz
        buzz: StreamBuzzModel = chat_analyst_agent.run_sync(chat.chat)
        if buzz.intent == ChatIntentEnum.UNKNOWN_CHAT:
            return
        # Store the buzz to DB
        await supabase_util.store_buzz(buzz)
    except Exception as e:
        print(f"Error>> process_chat: {str(e)}")
        raise


@router.post("/read-chats", tags=["tasks"])
async def read_chats_task():
    try:
        await read_live_chats()
    except Exception as e:
        print(f"Error>> read_chats_task: {str(e)}")


@router.post("/write-chats", tags=["tasks"])
async def write_chats_task():
    try:
        await write_live_chats()
    except Exception as e:
        print(f"Error>> write_chats_task: {str(e)}")
