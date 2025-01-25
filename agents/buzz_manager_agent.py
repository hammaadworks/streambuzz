from pydantic_ai import Agent, RunContext
from pydantic_ai.settings import ModelSettings
from constants.constants import MODEL, MODEL_RETRIES
from constants.prompts import STREAM_STARTER_AGENT_SYSTEM_PROMPT
from utils.youtube_util import validate_and_extract_youtube_id

# Create Agent Instance with System Prompt and Result Type
buzz_manager_agent = Agent(
    model=MODEL,
    name="stream_starter_agent",
    end_strategy="early",
    model_settings=ModelSettings(temperature=0.0),
    system_prompt=STREAM_STARTER_AGENT_SYSTEM_PROMPT,
    result_type=str,
    result_tool_name="start_stream",
    result_tool_description=(
        "get url from user query, validate the url and start the stream."
    ),
    result_retries=MODEL_RETRIES,
    deps_type=str,
)
"""
1. Get URL
2. Check if valid url
3. Get Id from URL
4. Get Metadata
5. Check if active stream link
6. store metadata in DB
7. Send acknowledgement message to FE with metadata
"""