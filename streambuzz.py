import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from agents import orchestrator_agent
from models.agent_models import AgentRequest, AgentResponse
from routers import chat_worker
from utils.supabase_util import fetch_conversation_history, store_message
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from routers.chat_worker import read_live_chats, write_live_chats

# Load environment variables
load_dotenv()

# Create the scheduler instance
scheduler = BackgroundScheduler()


# Define lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the scheduler
    scheduler.add_job(read_live_chats, "interval", seconds=30, id="30_sec_task")
    scheduler.add_job(write_live_chats, "interval", minutes=1, id="1_min_task")
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> bool:
    """Verify the bearer token against environment variable."""
    expected_token = os.getenv("API_BEARER_TOKEN")
    if not expected_token:
        raise HTTPException(
            status_code=500, detail="API_BEARER_TOKEN environment variable not set"
        )
    if credentials.credentials != expected_token:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return True


@app.get("/")
async def root():
    return {"message": "Chat Worker is up and running! Tasks have been Scheduled!"}


@app.post("/api/v1/streambuzz", response_model=AgentResponse)
async def sample_supabase_agent(
    request: AgentRequest, authenticated: bool = Depends(verify_token)
):
    try:
        # Fetch conversation history from the DB
        messages = await fetch_conversation_history(request.session_id, 3)

        # Store user's query
        await store_message(
            session_id=request.session_id, message_type="human", content=request.query
        )

        # Get agent's response
        agent_response = await orchestrator_agent.get_response(
            session_id=request.session_id, query=request.query, messages=messages
        )

        # Store agent's response
        await store_message(
            session_id=request.session_id,
            message_type="ai",
            content=agent_response,
            data={"request_id": request.request_id},
        )

        return AgentResponse(success=True)

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        # Store error message in conversation
        await store_message(
            session_id=request.session_id,
            message_type="ai",
            content="I apologize, but I encountered an error processing your request.",
            data={"error": str(e), "request_id": request.request_id},
        )
        return AgentResponse(success=False)
