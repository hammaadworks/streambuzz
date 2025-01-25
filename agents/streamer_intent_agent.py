from pydantic_ai import Agent, ModelRetry
from pydantic_ai.settings import ModelSettings

from constants.constants import MODEL, MODEL_RETRIES
from constants.enums import StreamerIntentEnum
from constants.prompts import STREAMER_INTENT_AGENT_SYSTEM_PROMPT


# Create Agent Instance with System Prompt and Result Type
streamer_intent_agent = Agent(
    model=MODEL,
    name="streamer_intent_agent",
    end_strategy="early",
    model_settings=ModelSettings(temperature=0.0),
    system_prompt=STREAMER_INTENT_AGENT_SYSTEM_PROMPT,
    result_type=str,
    result_tool_name="get_streamer_intent",
    result_tool_description=(
        "get the streamer intent to either start moderating, get current buzz, "
        "get next buzz or reply to buzz."
        ""
    ),
    result_retries=MODEL_RETRIES,
)


@streamer_intent_agent.result_validator
async def validate_get_streamer_intent(result: str) -> StreamerIntentEnum:
    """
    Validate the result from the streamer intent agent.

    Args:
        result (str): The result string to validate.

    Returns:
        StreamerIntentEnum: The validated streamer intent.

    Raises:
        ModelRetry: If the result is invalid.
    """
    # Validate the result and retry if invalid
    try:
        for intent in StreamerIntentEnum:
            if intent.name in result.strip().upper():
                return intent
    except ValueError as e:
        raise ModelRetry(f"Invalid streamer intent: {e}") from e
