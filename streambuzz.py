import os
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from agents import orchestrator
from constants.constants import (CHAT_READ_INTERVAL, CHAT_WRITE_INTERVAL,
                                 CONVERSATION_CONTEXT)
from exceptions.user_error import UserError
from models.agent_models import AgentRequest, AgentResponse
from routers import chat_worker
from routers.chat_worker import read_live_chats, write_live_chats
from utils.streamer_intent_util import classify_intent
from utils.supabase_util import fetch_conversation_history, store_message

# Load environment variables
load_dotenv()

# Create the scheduler instance
scheduler = BackgroundScheduler()


# Define lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the scheduler
    scheduler.add_job(read_live_chats, "interval", seconds=CHAT_READ_INTERVAL,
                      id="read_live_chats")
    scheduler.add_job(write_live_chats, "interval", seconds=CHAT_WRITE_INTERVAL,
                      id="write_live_chats")
    scheduler.start()
    print("Scheduler started...")

    # Yield control back to the app
    yield

    # Shutdown the scheduler
    scheduler.shutdown()
    print("Scheduler shut down...")


# Create the FastAPI app
app = FastAPI(lifespan=lifespan)
app.include_router(chat_worker.router)
security = HTTPBearer()

# noinspection PyTypeChecker
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


def verify_token(
        credentials: HTTPAuthorizationCredentials = Security(security), ) -> bool:
    """Verify the bearer token against environment variable."""
    expected_token = os.getenv("API_BEARER_TOKEN")
    if not expected_token:
        raise HTTPException(status_code=500,
                            detail="API_BEARER_TOKEN environment variable not set")
    if credentials.credentials != expected_token:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return True


@app.get("/")
async def root():
    intent = await classify_intent(
        "Start streaming: https://www.youtube.com/watch?v=Kt7hKHlArl8")
    return (f"Chat Worker is up and running! Tasks have been Scheduled! >> "
            f"{intent.value}")


# noinspection PyUnusedLocal
@app.post("/api/v1/streambuzz", response_model=AgentResponse)
async def sample_supabase_agent(request: AgentRequest,
                                authenticated: bool = Depends(verify_token)):
    try:
        # Fetch conversation history from the DB
        messages = await fetch_conversation_history(request.session_id,
                                                    CONVERSATION_CONTEXT)

        # Store user's query with files if present
        message_data = {"request_id": request.request_id}
        if request.files:
            message_data["files"] = request.files

        # Store user's query
        await store_message(session_id=request.session_id, message_type="human",
                            content=request.query, data=message_data)

        # Get agent's response
        agent_response = await orchestrator.get_response(request=request,
                                                         messages=messages)

        # Store agent's response
        await store_message(session_id=request.session_id, message_type="ai",
                            content=agent_response,
                            data={"request_id": request.request_id})

        return AgentResponse(success=True)
    except UserError as ue:
        user_error_string = str(ue)
        print(f"Error>> get_response: {user_error_string}")
        exception_response = await orchestrator.orchestrator_agent.run(
            user_prompt=f"Draft a small polite message to convey the following "
                        f"error.\n{user_error_string}")

        # Store agent's response
        await store_message(session_id=request.session_id, message_type="ai",
                            content=exception_response.data,
                            data={"request_id": request.request_id})

        return AgentResponse(success=True)
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        # Store error message in conversation
        await store_message(session_id=request.session_id,
                            message_type="ai",
                            content="I apologize, but I encountered an error "
                                    "processing your request.",
                            data={"error": str(e), "request_id": request.request_id}, )
        return AgentResponse(success=False)
