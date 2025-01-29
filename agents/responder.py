from constants.constants import MODEL_RETRIES, PYDANTIC_AI_MODEL
from constants.prompts import RESPONDER_SYSTEM_PROMPT
from pydantic_ai import Agent, RunContext
from pydantic_ai.settings import ModelSettings
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
    """Responds to a user query using Retrieval Augmented Generation (RAG).

    This tool first checks if a knowledge base exists for the given session ID.
    If a knowledge base is found, it retrieves relevant document chunks based on
    the user's query using embeddings. The retrieved chunks are then formatted and
    returned. If no knowledge base is found or no relevant chunks are retrieved,
    the function returns None, signaling the agent to fall back to the LLM.

    Args:
        ctx: The context of the current run, including the session ID as `ctx.deps`.
        user_query: The user's question or query string.

    Returns:
        A string containing formatted document chunks relevant to the user query,
        or None if no relevant information is found or an error occurs. The chunks
        are formatted with a header containing the document title, followed by the
        document content, with a separator between chunks.

    Raises:
        Exception: If an error occurs during the retrieval process. The error message
            is logged to the console and also returned as a string.
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
