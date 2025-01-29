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
"""The number of files accepted for processing."""
ACCEPTED_FILE_MIME = "text/plain"
"""The accepted MIME type of the file."""
ACCEPTED_FILE_EXTENSION = ".txt"
"""The accepted file extension."""
MAX_FILE_SIZE_MB = 5
"""Maximum file size in megabytes."""
MAX_FILE_SIZE_B = MAX_FILE_SIZE_MB * 1024 * 1024  # 5MB
"""Maximum file size in bytes."""


# Intents
CHAT_READ_INTERVAL = 30
"""Interval in seconds to read chat messages."""
CHAT_WRITE_INTERVAL = 60
"""Interval in seconds to write chat messages."""
CONVERSATION_CONTEXT = 3
"""Number of previous messages to include in the conversation context."""
START_STREAM_APPEND = f"\n\nFetching buzz in {CHAT_READ_INTERVAL} seconds..."
"""Message appended to start of stream."""
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
"""Examples of streamer intents and their corresponding phrases."""
CHAT_INTENT_EXAMPLES = {
    "QUESTION": [
        "What is your favorite game right now?",
        "How does machine learning work?",
        "Which GPU are you using for streaming?",
        "Can AI be used to improve gaming performance?",
    ],
    "CONCERN": [
        "The stream keeps buffering; is there an issue?",
        "I’m worried about how AI will affect jobs.",
        "My game keeps crashing after the latest update.",
        "The PC build you suggested doesn’t work for me.",
    ],
    "REQUEST": [
        "Can you play a round of Valorant next?",
        "Please review the new RTX 4090 GPU.",
        "Could you explain how neural networks work?",
        "Show us your gaming setup!",
    ],
    "UNKNOWN": [
        "Hello, great stream!",
        "LOL, that was epic!",
        "Good morning, everyone!",
        "Awesome content as always.",
    ],
}
"""Examples of chat intents and their corresponding phrases."""

# Model Constants
NLP_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
"""Sentence Transformer model for generating sentence embeddings."""
EMBEDDING_MODEL_NAME = "models/text-embedding-004"
"""Name of the embedding model."""
EMBEDDING_DIMENSIONS = 768
"""Dimensionality of the generated embeddings."""
CHUNK_SIZE = 3000
"""Size of text chunks used for processing."""
MODEL_RETRIES = 3
"""Number of retries for model calls."""

# Open Router Pydantic-AI model related constants
OPEN_ROUTER_BASE_URL = "https://openrouter.ai/api/v1"
"""Base URL for Open Router API."""
OPEN_ROUTER_MODEL_NAME = "gemini-2.0-flash-exp"
"""Name of the Open Router model."""
OPEN_ROUTER_CLIENT = OpenAI(
    base_url=OPEN_ROUTER_BASE_URL,
    api_key=os.getenv("OPEN_ROUTER_API_KEY"),
)
"""OpenAI client configured for Open Router."""
OPEN_ROUTER_MODEL = OpenAIModel(
    model_name=OPEN_ROUTER_MODEL_NAME,
    base_url=OPEN_ROUTER_BASE_URL,
    api_key=os.getenv("OPEN_ROUTER_API_KEY"),
)
"""Pydantic-AI OpenAI model configured for Open Router."""

# Gemini Pydantic-AI model related constants - testing
GEMINI_MODEL_NAME = "gemini-2.0-flash-exp"
"""Name of the Gemini model."""
GEMINI_MODEL = GeminiModel(
    model_name=GEMINI_MODEL_NAME, api_key=os.getenv("GEMINI_API_KEY")
)
"""Pydantic-AI Gemini model."""

# Model used in project
PYDANTIC_AI_MODEL = GEMINI_MODEL
"""The Pydantic-AI model used in the project."""

# YouTube API related constants
YOUTUBE_URL_REGEX = r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/[a-zA-Z0-9_\-]+"
"""Regex for matching YouTube URLs."""
ALLOWED_DOMAINS = ["youtube.com", "www.youtube.com", "youtu.be"]
"""Allowed domains for YouTube URLs."""
YOUTUBE_API_ENDPOINT = "https://www.googleapis.com/youtube/v3/videos"
"""Endpoint for YouTube API videos."""
YOUTUBE_LIVE_API_ENDPOINT = "https://www.googleapis.com/youtube/v3/liveChat/messages"
"""Endpoint for YouTube API live chat messages."""

# Supabase setup constants
SUPABASE_CLIENT = create_client(
    os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY")
)
"""Supabase client."""

# Table names
MESSAGES = "messages"
"""Name of the messages table."""
YT_KEYS = "youtube_keys"
"""Name of the youtube keys table."""
YT_STREAMS = "youtube_streams"
"""Name of the youtube streams table."""
YT_BUZZ = "youtube_buzz"
"""Name of the youtube buzz table."""
YT_REPLY = "youtube_reply"
"""Name of the youtube reply table."""
STREAMER_KB = "streamer_knowledge"
"""Name of the streamer knowledge table."""
