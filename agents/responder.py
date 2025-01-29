from pydantic_ai import Agent, RunContext
from pydantic_ai.settings import ModelSettings

from constants.constants import MODEL_RETRIES, PYDANTIC_AI_MODEL
from constants.prompts import RESPONDER_SYSTEM_PROMPT
from utils import supabase_util
from utils.rag_util import get_embedding

# Create Agent Instance with System Prompt and Result Type
responder_agent = Agent(
    model=PYDANTIC_AI_MODEL,
    name="responder_agent",
    end_strategy="early",
    model_settings=ModelSettings(temperature=0.0),
    system_prompt=RESPONDER_SYSTEM_PROMPT,
    result_type=str,
    result_tool_name="respond",
    result_tool_description="respond queries using RAG. If no sufficient "
                            "information is found in knowledge base then "
                            "default to LLM to generate the response",
    result_retries=MODEL_RETRIES,
)


@responder_agent.tool
async def respond(ctx: RunContext[str], user_query: str) -> str:
    """
        
    Args:
        ctx: The context including the session_id
        user_query: The user's question or query
        
    Returns:
        A formatted answer to the user's query primarily using RAG, else LLM.
    """
    try:
        # Check if session_id has knowledge base
        file_name: str = await supabase_util.get_kb_file_name(session_id=ctx.deps)
        if not file_name:
            return None

        # Get the embedding for the query
        query_embedding = await get_embedding(user_query)

        # Query Supabase for relevant documents
        result = await supabase_util.get_matching_chunks(
            query_embedding=query_embedding, session_id=ctx.deps
        )

        if not result:
            return None

        # Format the results
        formatted_chunks = []
        for doc in result:
            chunk_text = f"""# {doc['title']}\n{doc['content']}"""
            formatted_chunks.append(chunk_text)

        # Join all chunks with a separator
        return "\n---\n".join(formatted_chunks)

    except Exception as e:
        print(f"Error retrieving documentation: {e}")
        return f"Error retrieving documentation: {str(e)}"
