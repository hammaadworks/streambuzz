import json
from collections import defaultdict
from typing import Any, Dict, List

from fastapi import APIRouter

from agents.orchestrator import orchestrator_agent
from constants.constants import YOUTUBE_LIVE_API_ENDPOINT
from constants.enums import BuzzStatusEnum, ChatIntentEnum
from constants.prompts import REPLY_SUMMARISER_PROMPT
from models.agent_models import ProcessFoundBuzz
from models.youtube_models import WriteChatModel
from utils import supabase_util, youtube_util
from utils.supabase_util import store_message
from utils.youtube_util import get_youtube_api_keys
from ..agents.responder import responder_agent

# Create API router for managing live chats
router = APIRouter()


async def process_buzz():
    """
    1. Get all id, buzz_type and original_chat of buzz in FOUND state
    2. Update fetched ids as PROCESSING
    2. For each buzz
        - call responder agent to generate response
        - store response in DB YT_BUZZ against the id and mark it ACTIVE
        - if error, update status to FOUND
    """
    found_buzz_list = await supabase_util.get_found_buzz()
    found_buzz_object_list = [ProcessFoundBuzz(**buzz) for buzz in found_buzz_list]
    if not found_buzz_object_list:
        return
    found_buzz_id_list = [buzz.id for buzz in found_buzz_object_list]
    await supabase_util.update_buzz_status_batch_by_id(
        id_list=found_buzz_id_list, buzz_status=BuzzStatusEnum.PROCESSING.value
    )
    for buzz in found_buzz_object_list:
        try:
            response = await responder_agent.run(
                user_prompt=f"{ChatIntentEnum(buzz.buzz_type)}: "
                            f"{buzz.original_chat}",
                result_type=str
            )
            await supabase_util.update_buzz_response_by_id(
                id=buzz.id,
                generated_response=response.data
            )
        except Exception as e:
            print(f"Error>> process_buzz: {str(e)}")
            await supabase_util.update_buzz_status_by_id(
                id=buzz.id, buzz_status=BuzzStatusEnum.FOUND.value
            )
            raise


async def read_live_chats():
    """
    1. Get all active stream sessions
    2. For each active session
        - call YT API to get live chat message list, use next_chat_page if available
        - is stream inactive, deactivate stream
        - update next_chat_page
        - for each chat in the list
            - get chat intent
            - if intent in [Question, Concern, Request], store in DB YT_BUZZ
    3. Call process_buzz to generate response of the buzz
    """
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
                        user_prompt=f"{REPLY_SUMMARISER_PROMPT}\n{raw_reply}",
                        result_type=str,
                    )
                    result.append(
                        WriteChatModel(
                            session_id=session_id,
                            live_chat_id=live_chat_id,
                            retry_count=retry_count,
                            reply=raw_reply,
                            reply_summary=reply_summary,
                        )
                    )
        return result
    except Exception as e:
        print(f"Error>> group_chats_by_session_id: {str(e)}")
        raise


async def write_live_chats():
    """
    1. Get session_id, live_chat_id and reply from YT_REPLY table where is_written=No
    2. 
    """
    
    try:
        # Get unwritten chats from YT_REPLY table
        # unwritten_chats_query_response = await supabase_util.get_unwritten_chats()
        unwritten_chats_query_response = []
        if not unwritten_chats_query_response:
            return
        grouped_chats: List[WriteChatModel] = await group_chats_by_session_id(
            unwritten_chats_query_response
        )

        # Call insert YouTube api on max retries in loop for each of the sessions
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
                    url=YOUTUBE_LIVE_API_ENDPOINT,
                    params=params,
                    payload=payload,
                    api_keys=get_youtube_api_keys(),
                )
                # await mark_existing_buzz_written(reply.session_id)
                await store_message(
                    session_id=reply.session_id,
                    message_type="ai",
                    content=f"StreamBuzz Bot: I've replied this on"
                            f" live chat\n{reply.reply_summary}",
                    data={"reply_dump": reply.model_dump()},
                )
            except Exception as e:
                print(f"Error>> write_live_chats: {reply.session_id}\n{str(e)}")
                raise
        # if success = update status to written session_id and live_chat_id. Respond
        # that replies have been posted to the DB messages
        # if stream_inactive = deactivate
        # if failed = get retry count; if retry count = 3: deactivate or retry count
        # = +1
    except Exception as e:
        print(f"Error>> write_live_chats: {str(e)}")
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
