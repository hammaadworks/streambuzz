import json
from collections import defaultdict
from typing import Any, Dict, List

from fastapi import APIRouter

from agents.orchestrator import orchestrator_agent
from agents.responder import responder_agent
from constants.constants import YOUTUBE_LIVE_API_ENDPOINT
from constants.enums import BuzzStatusEnum, ChatIntentEnum
from constants.prompts import REPLY_SUMMARISER_PROMPT
from models.agent_models import ProcessFoundBuzz
from models.youtube_models import StreamBuzzModel, WriteChatModel
from utils import intent_util, supabase_util, youtube_util
from utils.supabase_util import store_message
from utils.youtube_util import get_youtube_api_keys

# Create API router for managing live chats
router = APIRouter()


async def process_buzz():
    """
    Processes buzzes that are in the 'FOUND' state.

    This function retrieves buzzes in the 'FOUND' state from the database,
    updates their status to 'PROCESSING', and then uses a responder agent to
    generate a response for each buzz. The generated response is stored back
    in the database, and the buzz status is updated to 'ACTIVE'. If any error
    occurs during the process, the buzz status is set back to 'FOUND'.

    Raises:
        Exception: If any error occurs during the processing of a buzz,
            the exception is caught, logged, and re-raised after setting the
            buzz status back to 'FOUND'.
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
                user_prompt=f"Generate response within 400 words for this "
                            f"{ChatIntentEnum(buzz.buzz_type)}:\n{buzz.original_chat}",
                result_type=str,
            )
            await supabase_util.update_buzz_response_by_id(
                id=buzz.id, generated_response=response.data
            )
        except Exception as e:
            print(f"Error>> process_buzz: {str(e)}")
            await supabase_util.update_buzz_status_by_id(
                id=buzz.id, buzz_status=BuzzStatusEnum.FOUND.value
            )
            raise


async def process_chat_messages(chat_list: List[Dict[str, Any]], session_id: str):
    """
    Processes a list of chat messages for a given session.

    This function iterates through a list of chat messages, classifies
    the intent of each message, and if the intent is not 'UNKNOWN', stores
    the message as a 'buzz' in the database with a 'FOUND' status.
    If any error occurs during the processing of a chat message, it logs the
    error along with the chat message that caused the error.

    Args:
        chat_list (List[Dict[str, Any]]): A list of dictionaries, where each
            dictionary represents a chat message and contains at least the keys
            'original_chat' and 'author'.
        session_id (str): The ID of the session to which the chat messages belong.

    Raises:
        Exception: If an error occurs during the processing of a chat message,
            the exception is caught, logged, and not re-raised.
    """
    for chat in chat_list:
        try:
            original_chat, author = chat["original_chat"], chat["author"]
            chat_intent: ChatIntentEnum = intent_util.classify_chat_intent(
                original_chat
            )

            if chat_intent != ChatIntentEnum.UNKNOWN:
                await supabase_util.store_buzz(
                    StreamBuzzModel(
                        session_id=session_id,
                        original_chat=original_chat,
                        author=author,
                        buzz_status=BuzzStatusEnum.FOUND.value,
                        buzz_type=chat_intent.value,
                        generated_response="",
                    )
                )
        except Exception as e:
            # Log the exception for the chat-level failure
            print(f"Error processing chat: {chat}. Exception: {e}")


async def process_active_streams(
    active_streams: List[Dict[str, Any]], api_keys: Dict[str, str]
):
    """
    Processes all active streams.

    This function iterates through a list of active streams, fetches the latest
    chat messages for each stream using the YouTube API, and then processes the
    chat messages. If any error occurs during the processing of a stream,
    it logs the error along with the stream that caused the error.

    Args:
        active_streams (List[Dict[str, Any]]): A list of dictionaries, where each
            dictionary represents an active stream and contains at least the keys
            'session_id', 'live_chat_id', and 'next_chat_page'.
        api_keys (Dict[str, str]): A dictionary containing YouTube API keys.

    Raises:
        Exception: If an error occurs during the processing of a stream,
            the exception is caught, logged, and not re-raised.
    """
    for stream in active_streams:
        try:
            session_id, live_chat_id, next_chat_page = (
                stream["session_id"],
                stream["live_chat_id"],
                stream["next_chat_page"],
            )
            chat_list = await youtube_util.get_live_chat_messages(
                session_id, live_chat_id, next_chat_page, api_keys
            )
            if not chat_list:
                return

            await process_chat_messages(chat_list, session_id)

        except Exception as e:
            # Log the exception for the stream-level failure
            print(f"Error processing stream: {stream}. Exception: {e}")


async def read_live_chats():
    """
    Reads and processes live chat messages from active YouTube streams.

    This function retrieves all active stream sessions, fetches live chat
    messages for each session using the YouTube API, and determines the intent
    of each chat message. If the intent is one of [Question, Concern, Request],
    the chat is stored in the database as a 'buzz'. It also updates the
    `next_chat_page` token for pagination and deactivates streams if they
    are no longer active. Finally, it calls `process_buzz` to generate
    responses for the newly created buzzes.
    """
    # Get active stream sessions
    api_keys = get_youtube_api_keys()
    active_streams = await supabase_util.get_active_streams()
    if active_streams:
        await process_active_streams(active_streams, api_keys)
    await process_buzz()


async def group_chats_by_session_id(
    unwritten_chats: List[Dict[str, Any]],
) -> List[WriteChatModel]:
    """
    Groups unwritten chat messages by session ID, live chat ID, and retry count.

    This function takes a list of unwritten chat messages and groups them
    based on their session ID and live chat ID. It then summarizes the grouped
    messages using an orchestrator agent and creates `WriteChatModel`
    instances for each group. The `WriteChatModel` instances contain the
    original concatenated replies and the summarized reply.

    Args:
        unwritten_chats (List[Dict[str, Any]]): A list of dictionaries, where each
            dictionary represents an unwritten chat message and contains at
            least the keys 'session_id', 'live_chat_id', and 'reply'.

    Returns:
        List[WriteChatModel]: A list of `WriteChatModel` instances, each
            representing a group of summarized chat messages.

    Raises:
        Exception: If an error occurs during the grouping or summarization
            process, the exception is caught, logged, and re-raised.
    """
    try:
        # Prepare the desired output
        grouped_chats = defaultdict(lambda: defaultdict(list))

        # Group chats by session_id, live_chat_id
        for row in unwritten_chats:
            grouped_chats[row["session_id"]][row["live_chat_id"]].append(row["reply"])

        # Populate WriteChatModel instances
        result: List[WriteChatModel] = []
        for session_id, live_chat_groups in grouped_chats.items():
            for live_chat_id, replies in live_chat_groups.items():
                raw_reply = ". ".join(replies)
                reply_summary = await orchestrator_agent.run(
                    user_prompt=f"{REPLY_SUMMARISER_PROMPT}\n{raw_reply}",
                    result_type=str,
                )
                result.append(
                    WriteChatModel(
                        session_id=session_id,
                        live_chat_id=live_chat_id,
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
    Writes summarized chat replies to YouTube live chats.

    This function retrieves unwritten chat replies from the database, groups them
    by session ID and live chat ID, and then uses the YouTube API
    to post the summarized replies to the corresponding live chats. It also
    updates the database to indicate that the replies have been written and
    stores a message in the database indicating that the bot has replied.
    The function handles retries and deactivates streams if necessary.

    Raises:
        Exception: If any error occurs during the process, such as fetching
            unwritten chats, grouping them, calling the YouTube API, or
            updating the database, the exception is caught, logged, and
            re-raised.
    """
    try:
        # Get unwritten chats from YT_REPLY table
        unwritten_chats_query_response = await supabase_util.get_unwritten_replies()
        if not unwritten_chats_query_response:
            return
        grouped_chats: List[WriteChatModel] = await group_chats_by_session_id(
            unwritten_chats_query_response
        )

        # Update status of those live_chat_id to PENDING
        for reply in grouped_chats:
            await supabase_util.mark_replies_pending(reply.live_chat_id)

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
                await supabase_util.mark_replies_success(reply.live_chat_id)
                await store_message(
                    session_id=reply.session_id,
                    message_type="ai",
                    content=f"StreamBuzz Bot: Hey there! I have just dropped a reply in the live chat:\n{reply.reply_summary}\n— check it out!",
                    data={"reply_dump": reply.model_dump()},
                )
            except Exception as e:
                print(f"Error>> write_live_chats: {str(reply)}\n{str(e)}")
                await supabase_util.mark_replies_failed(reply.live_chat_id)
                raise
    except Exception as e:
        print(f"Error>> write_live_chats: {str(e)}")
        raise


@router.post("/read-chats", tags=["tasks"])
async def read_chats_task():
    """
    API endpoint to initiate the reading of live chat messages.

    This endpoint triggers the `read_live_chats` function, which handles
    fetching and processing live chat messages from active YouTube streams.

    Raises:
        Exception: If an error occurs during the execution of
            `read_live_chats`, the exception is caught, logged, and
            not re-raised.
    """
    try:
        print("Started async background task>> read_live_chats")
        await read_live_chats()
    except Exception as e:
        print(f"Error>> read_chats_task: {str(e)}")


@router.post("/write-chats", tags=["tasks"])
async def write_chats_task():
    """
    API endpoint to initiate the writing of summarized chat replies.

    This endpoint triggers the `write_live_chats` function, which handles
    posting summarized chat replies to YouTube live chats.

    Raises:
        Exception: If an error occurs during the execution of
            `write_live_chats`, the exception is caught, logged, and
            not re-raised.
    """
    try:
        print("Started async background task>> write_live_chats")
        await write_live_chats()
    except Exception as e:
        print(f"Error>> write_chats_task: {str(e)}")
