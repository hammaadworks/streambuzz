from pydantic_ai import Agent
from pydantic_ai.messages import ModelRequest, ModelResponse
from pydantic_ai.settings import ModelSettings
from typing import List
from constants.constants import MODEL, MODEL_RETRIES, START_STREAM_APPEND
from constants.enums import StreamerIntentEnum
from constants.prompts import ORCHESTRATOR_AGENT_SYSTEM_PROMPT
from exceptions.user_error import UserError
from .buzz_manager_agent import buzz_manager_agent
from .stream_starter_agent import stream_starter_agent
from .streamer_intent_agent import streamer_intent_agent

# Create Agent Instance with System Prompt and Result Type
orchestrator_agent = Agent(
    model=MODEL,
    name="orchestrator_agent",
    end_strategy="early",
    model_settings=ModelSettings(temperature=0.0),
    system_prompt=ORCHESTRATOR_AGENT_SYSTEM_PROMPT,
    result_type=str,
    result_retries=MODEL_RETRIES,
    deps_type=str,
)


async def get_response(
        session_id: str, query: str, messages: List[ModelRequest | ModelResponse]
) -> str:
    """
    Calls required agents to complete the task and returns the response.

    Args:
        session_id (str): The session ID.
        query (str): The user query.
        messages (List[ModelRequest | ModelResponse]): The message history.

    Returns:
        str: The response from the orchestrator agent.

    Raises:
        UserError: If there is an error with the user input.
        Exception: If there is a general error.
    """
    try:
        # Get streamer's intent
        streamer_intent = await streamer_intent_agent.run(user_prompt=query)
        print(f"{query=}>> {streamer_intent.data.name=}")

        # Perform task based on streamer's intent
        if streamer_intent.data == StreamerIntentEnum.START_STREAM_STREAMER_INTENT:
            result = await stream_starter_agent.run(user_prompt=query, deps=session_id)
            return result.data + START_STREAM_APPEND
        elif (
                streamer_intent.data == StreamerIntentEnum.GET_CURRENT_BUZZ_STREAMER_INTENT
        ):
            result = buzz_manager_agent.run_sync(
                user_prompt="Get the current buzz", deps=session_id
            )
        elif streamer_intent.data == StreamerIntentEnum.GET_NEXT_BUZZ_STREAMER_INTENT:
            result = buzz_manager_agent.run_sync(
                user_prompt="Get the next buzz", deps=session_id
            )
        elif streamer_intent.data == StreamerIntentEnum.REPLY_TO_BUZZ_STREAMER_INTENT:
            # todo: replies generated should be unique for a given link in the session.
            result = buzz_manager_agent.run_sync(
                user_prompt=f"Reply by extracting messages in {query} and {messages[:2]}",
                deps=session_id,
            )
        else:
            result = await orchestrator_agent.run(
                user_prompt=query, message_history=messages
            )

        return result.data
    except UserError as ue:
        user_error_string = str(ue)
        print(f"Error>> get_response: {user_error_string}")
        result = await orchestrator_agent.run(
            user_prompt=f"Draft a small polite message to convey the following error.\n{user_error_string}"
        )
        return result.data
    except Exception as e:
        print(f"Error>> get_response: {str(e)}")
        raise
