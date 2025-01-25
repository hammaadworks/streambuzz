from pydantic_ai import Agent, RunContext
from pydantic_ai.settings import ModelSettings
from typing import Dict, Any
from constants.constants import MODEL, MODEL_RETRIES
from constants.prompts import STREAM_STARTER_AGENT_SYSTEM_PROMPT
from exceptions.user_error import UserError
from models.youtube_models import StreamMetadata, StreamMetadataDB
from utils import supabase_util
from utils.youtube_util import validate_and_extract_youtube_id, get_stream_metadata, deactivate_session

# Create Agent Instance with System Prompt and Result Type
stream_starter_agent = Agent(
    model=MODEL,
    name="stream_starter_agent",
    end_strategy="early",
    model_settings=ModelSettings(temperature=0.0),
    system_prompt=STREAM_STARTER_AGENT_SYSTEM_PROMPT,
    result_type=str,
    result_tool_name="start_stream",
    result_tool_description="get url from user query, validate the url and start the stream.",
    result_retries=MODEL_RETRIES,
    deps_type=str,
)


def get_live_chat_id(metadata):
    """
    Extract the live chat ID from the metadata.

    Args:
        metadata (dict): The metadata containing live streaming details.

    Returns:
        str: The live chat ID.

    Raises:
        UserError: If the live chat ID cannot be fetched.
    """
    try:
        return metadata.get("liveStreamingDetails").get("activeLiveChatId")
    except Exception as e:
        print(f"Error fetching live chat id: {str(e)}")
        raise UserError("Inactive or invalid stream link.")


def populate_metadata_class(video_id, snippet, live_chat_id) -> StreamMetadata:
    """
    Populate the StreamMetadata class with video details.

    Args:
        video_id (str): The video ID.
        snippet (dict): The snippet containing video details.
        live_chat_id (str): The live chat ID.

    Returns:
        StreamMetadata: The populated StreamMetadata instance.
    """
    return StreamMetadata(

        title=snippet.get("title").strip(),
        channel_title=snippet.get("channelTitle"),
        thumbnail_url=snippet.get("thumbnails").get("high").get("url"),

    )


@stream_starter_agent.tool
async def start_stream(
        ctx: RunContext[str], url: str
) -> Dict[str, Any]:
    """
    Start a stream by validating the URL and fetching stream metadata.

    Args:
        ctx (RunContext[str]): The run context containing dependencies.
        url (str): The YouTube URL to validate and start the stream.

    Returns:
        dict: The stream metadata.

    Raises:
        UserError: If there is an error with the user input.
        Exception: If there is a general error.
    """
    try:
        video_id = await validate_and_extract_youtube_id(url=url)
        video_metadata = await get_stream_metadata(video_id=video_id)
        metadata_items = video_metadata.get("items")

        if not metadata_items:
            raise UserError("Invalid YouTube stream link.")

        video_id = metadata_items[0].get("id")
        snippet = metadata_items[0].get("snippet")
        live_chat_id = get_live_chat_id(metadata_items[0])
        stream_metadata = populate_metadata_class(video_id, snippet, live_chat_id)

        # Update flag for session_id
        session_id = ctx.deps
        await deactivate_session(session_id)
        
        # Store metadata in DB
        stream_metadata_db = StreamMetadataDB(
            **stream_metadata.model_dump(), video_id=video_id, live_chat_id=live_chat_id, session_id=session_id,
            next_chat_page=None
        )
        await supabase_util.start_stream(stream_metadata_db)

        return stream_metadata.model_dump()
    except UserError as ue:
        print(f"Error>> start_stream: {str(ue)}")
        raise
    except Exception as e:
        print(f"Error>> start_stream: {str(e)}")
        raise
