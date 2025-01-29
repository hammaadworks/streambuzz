from typing import List

from pydantic_ai import Agent
from pydantic_ai.messages import ModelRequest, ModelResponse
from pydantic_ai.settings import ModelSettings

from constants.constants import MODEL_RETRIES, PYDANTIC_AI_MODEL, START_STREAM_APPEND
from constants.enums import StreamerIntentEnum
from constants.prompts import ORCHESTRATOR_AGENT_SYSTEM_PROMPT
from exceptions.user_error import UserError
from models.agent_models import AgentRequest
from utils import intent_util
from utils.rag_util import create_knowledge_base
from .buzz_master import buzz_master_agent
from .stream_starter import stream_starter_agent
from .responder import responder_agent

# Create Agent Instance with System Prompt and Result Type
orchestrator_agent = Agent(
    model=PYDANTIC_AI_MODEL,
    name="orchestrator_agent",
    end_strategy="early",
    model_settings=ModelSettings(temperature=0.0),
    system_prompt=ORCHESTRATOR_AGENT_SYSTEM_PROMPT,
    result_type=str,
    result_retries=MODEL_RETRIES,
    deps_type=str,
)


async def get_response(
    request: AgentRequest,
    human_messages: list[str],
    messages: List[ModelRequest | ModelResponse],
) -> str:
    try:
        # Make file RAG ready
        if request.files:
            await create_knowledge_base(request)

        # Get streamer's buzz_type
        streamer_intent: StreamerIntentEnum = (
            await intent_util.classify_streamer_intent(
                messages=human_messages, query=request.query
            )
        )
        print(f"{request.query=}>> {streamer_intent.name=}")

        # Perform task based on streamer's buzz_type
        if streamer_intent == StreamerIntentEnum.START_STREAM:
            agent_result = await stream_starter_agent.run(
                user_prompt=request.query, deps=request.session_id, result_type=str
            )
            response = agent_result.data + START_STREAM_APPEND
        elif streamer_intent == StreamerIntentEnum.CURRENT_BUZZ:
            agent_result = await buzz_master_agent.run(
                user_prompt="Get current buzz.", deps=request.session_id, result_type=str
            )
            response = agent_result.data
        elif streamer_intent == StreamerIntentEnum.NEXT_BUZZ:
            agent_result = await buzz_master_agent.run(
                user_prompt="Get next buzz.", deps=request.session_id, result_type=str
            )
            response = agent_result.data
        elif streamer_intent == StreamerIntentEnum.POST_REPLY:
            agent_result = await buzz_master_agent.run(
                user_prompt=f"Extract and store reply from this message:\n{request.query}",
                deps=request.session_id,
                result_type=str
            )
            response = agent_result.data
        else:
            agent_result = await responder_agent.run(
                user_prompt=request.query, deps= request.session_id,result_type=str, message_history=messages
            )
            response = agent_result.data

        return response
    except UserError as ue:
        print(f"Error>> get_response: {str(ue)}")
        raise
    except Exception as e:
        print(f"Error>> get_response: {str(e)}")
        raise
