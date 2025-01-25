from pydantic_ai import Agent, ModelRetry
from pydantic_ai.settings import ModelSettings

from constants.constants import MODEL, MODEL_RETRIES
from constants.enums import ChatIntentEnum
from constants.prompts import CHAT_ANALYST_AGENT_SYSTEM_PROMPT
from models.youtube_models import BuzzModel


# Create Agent Instance with System Prompt and Result Type
chat_analyst_agent = Agent(
    model=MODEL,
    name="chat_analyst_agent",
    end_strategy="early",
    model_settings=ModelSettings(temperature=0.0),
    system_prompt=CHAT_ANALYST_AGENT_SYSTEM_PROMPT,
    result_type=BuzzModel,
    result_tool_name="analyse_chat",
    result_tool_description="classify and summarize chat into question, concern or request based on intent",
    result_retries=MODEL_RETRIES,
)


@chat_analyst_agent.result_validator
async def validate_get_chat_analyst(result: BuzzModel) -> BuzzModel:
    """
    Validate the result from the chat analyst agent.

    Args:
        result (BuzzModel): The result model to validate.

    Returns:
        BuzzModel: The validated result model.

    Raises:
        ModelRetry: If the result is invalid.
    """
    # Validate the result and retry if invalid
    if not isinstance(result, BuzzModel):
        raise ModelRetry("Invalid chat analysis result type.")
    # Validate the intent enum
    try:
        for intent in ChatIntentEnum:
            if intent.name in result.intent.strip().upper():
                return BuzzModel(summary=result.summary, intent=intent.value)
    except ValueError as e:
        raise ModelRetry(f"Invalid chat intent: {e}") from e
