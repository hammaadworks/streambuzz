from pydantic_ai import Agent, RunContext
from pydantic_ai.settings import ModelSettings

from constants.constants import CHAT_WRITE_INTERVAL, MODEL_RETRIES, PYDANTIC_AI_MODEL
from constants.enums import StateEnum
from constants.prompts import BUZZ_MASTER_SYSTEM_PROMPT
from exceptions.user_error import UserError
from models.youtube_models import StreamMetadataDB, WriteChatModel
from utils import supabase_util

# Create Agent Instance with System Prompt and Result Type
buzz_master_agent = Agent(
    model=PYDANTIC_AI_MODEL,
    name="buzz_master_agent",
    end_strategy="early",
    model_settings=ModelSettings(temperature=0.0),
    system_prompt=BUZZ_MASTER_SYSTEM_PROMPT,
    result_type=str,
    result_tool_name="execute_task",
    result_tool_description="execute tasks and return user friendly response",
    result_retries=MODEL_RETRIES,
    deps_type=str,
)


@buzz_master_agent.tool
async def get_current_buzz(ctx: RunContext[str]) -> str:
    return await supabase_util.get_current_buzz(session_id=ctx.deps)


@buzz_master_agent.tool
async def get_next_buzz(ctx: RunContext[str]) -> str:
    await supabase_util.mark_current_buzz_inactive(session_id=ctx.deps)
    return await supabase_util.get_current_buzz(session_id=ctx.deps)


@buzz_master_agent.tool
async def store_reply(ctx: RunContext[str], reply: str) -> str:
    try:
        active_stream: StreamMetadataDB = await supabase_util.get_active_stream(session_id=ctx.deps)
        if not active_stream:
            raise UserError("No active stream found.")
        await supabase_util.store_reply(WriteChatModel(session_id=active_stream.session_id,
                                                       live_chat_id=active_stream.live_chat_id,
                                                       retry_count=0,
                                                       reply=reply,
                                                       is_written=StateEnum.NO.value))
        return f"Your reply is acknowledged. Replies within time slot of {CHAT_WRITE_INTERVAL} seconds will be cumulated and posted to live chat."
    except Exception as e:
        raise UserError(f"Error storing reply: {str(e)}")
