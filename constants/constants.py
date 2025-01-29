import os

from dotenv import load_dotenv
from openai import OpenAI
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel
from sentence_transformers import SentenceTransformer
from supabase import create_client

load_dotenv()

# Files
ACCEPTED_FILE_QUANTITY = 1
ACCEPTED_FILE_MIME = "text/plain"
ACCEPTED_FILE_EXTENSION = ".txt"
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_B = MAX_FILE_SIZE_MB * 1024 * 1024  # 5MB

# Intents
CHAT_READ_INTERVAL = 30
CHAT_WRITE_INTERVAL = 60
CONVERSATION_CONTEXT = 3
START_STREAM_APPEND = f"\n\nFetching buzz in {CHAT_READ_INTERVAL} seconds..."
STREAMER_INTENT_EXAMPLES = {
    "START_STREAM": [
        "Start the stream",
        "Begin streaming",
        "Initiate the live stream",
        "Start stream moderation",
        "Begin streaming moderation",
        "Initiate the live stream moderation",
        "Start moderating",
        "Begin moderating",
        "Moderate this",
        ],
    "CURRENT_BUZZ": [
        "Get current",
        "Display current",
        "What's now?",
        "What's current",
        "Get current buzz",
        "Display current buzz",
        "Which buzz",
        "What is the current buzz?",
        ],
    "NEXT_BUZZ": [
        "Get next",
        "Display next",
        "What's next?",
        "Tell me next",
        "Display next buzz",
        "Show next buzz",
        "What is the next buzz?",
        "What comes after this buzz?",
        ],
    "POST_REPLY": [
        "Post a reply to this comment",
        "Respond to the message",
        "Write a reply",
        "Reply as",
        "Post reply",
        "Answer as",
        ],
    "UNKNOWN": ["Random query", "Unrelated question", "This doesn't fit any category"],
    }
CHAT_INTENT_EXAMPLES = {
    "QUESTION": [
        "What is your favorite game right now?",
        "How does machine learning work?",
        "Which GPU are you using for streaming?",
        "Can AI be used to improve gaming performance?"
    ],
    "CONCERN": [
        "The stream keeps buffering; is there an issue?",
        "I’m worried about how AI will affect jobs.",
        "My game keeps crashing after the latest update.",
        "The PC build you suggested doesn’t work for me."
    ],
    "REQUEST": [
        "Can you play a round of Valorant next?",
        "Please review the new RTX 4090 GPU.",
        "Could you explain how neural networks work?",
        "Show us your gaming setup!"
    ],
    "UNKNOWN": [
        "Hello, great stream!",
        "LOL, that was epic!",
        "Good morning, everyone!",
        "Awesome content as always."
    ]
}

# Model Constants
NLP_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_MODEL_NAME = "models/text-embedding-004"
EMBEDDING_DIMENSIONS = 768
CHUNK_SIZE = 3000
MODEL_RETRIES = 3

# Open Router Pydantic-AI model related constants
OPEN_ROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPEN_ROUTER_MODEL_NAME = "gemini-2.0-flash-exp"
OPEN_ROUTER_CLIENT = OpenAI(
    base_url=OPEN_ROUTER_BASE_URL,
    api_key=os.getenv("OPEN_ROUTER_API_KEY"),
    )
OPEN_ROUTER_MODEL = OpenAIModel(
    model_name=OPEN_ROUTER_MODEL_NAME,
    base_url=OPEN_ROUTER_BASE_URL,
    api_key=os.getenv("OPEN_ROUTER_API_KEY"),
    )

# Gemini Pydantic-AI model related constants - testing
GEMINI_MODEL_NAME = "gemini-2.0-flash-exp"
GEMINI_MODEL = GeminiModel(
    model_name=GEMINI_MODEL_NAME, api_key=os.getenv("GEMINI_API_KEY")
    )

# Model used in project
PYDANTIC_AI_MODEL = GEMINI_MODEL

# YouTube API related constants
YOUTUBE_URL_REGEX = r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/[a-zA-Z0-9_\-]+"
ALLOWED_DOMAINS = ["youtube.com", "www.youtube.com", "youtu.be"]
YOUTUBE_API_ENDPOINT = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_LIVE_API_ENDPOINT = "https://www.googleapis.com/youtube/v3/liveChat/messages"

# Supabase setup constants
SUPABASE_CLIENT = create_client(
    os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY")
    )

# Table names
MESSAGES = "messages"
YT_KEYS = "youtube_keys"
YT_STREAMS = "youtube_streams"
YT_BUZZ = "youtube_buzz"
YT_REPLY = "youtube_reply"
STREAMER_KB = "streamer_knowledge"