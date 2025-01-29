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
"""Examples of streamer intents and their corresponding phrases.

    This dictionary maps intent names (keys) to lists of example phrases (values)
    that a streamer might use to trigger that intent.
"""
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
"""Examples of chat intents and their corresponding phrases.

    This dictionary maps intent names (keys) to lists of example phrases (values)
    that a chat user might use to express that intent.
"""

# Model Constants
NLP_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
"""Sentence Transformer model for generating sentence embeddings.

    This model is used to convert text into numerical vectors that capture semantic meaning.
"""
EMBEDDING_MODEL_NAME = "models/text-embedding-004"
"""Name of the embedding model.

    This string represents the specific model name used for generating embeddings.
"""
EMBEDDING_DIMENSIONS = 768
"""Dimensionality of the generated embeddings.

    This integer represents the number of dimensions in the vector space where text
    is embedded.
"""
CHUNK_SIZE = 3000
"""Size of text chunks used for processing.

    This integer defines the maximum number of characters to consider when processing
    text in chunks.
"""
MODEL_RETRIES = 3
"""Number of retries for model calls.

    This integer specifies the maximum number of times to retry a model call in case
    of failure.
"""

# Open Router Pydantic-AI model related constants
OPEN_ROUTER_BASE_URL = "https://openrouter.ai/api/v1"
"""Base URL for Open Router API.

    This string defines the base URL used to make API requests to Open Router.
"""
OPEN_ROUTER_MODEL_NAME = "gemini-2.0-flash-exp"
"""Name of the Open Router model.

    This string specifies the name of the model to be used from the Open Router API.
"""
OPEN_ROUTER_CLIENT = OpenAI(
    base_url=OPEN_ROUTER_BASE_URL,
    api_key=os.getenv("OPEN_ROUTER_API_KEY"),
)
"""OpenAI client configured for Open Router.

    This instance of the OpenAI client is configured to use the Open Router API.
"""
OPEN_ROUTER_MODEL = OpenAIModel(
    model_name=OPEN_ROUTER_MODEL_NAME,
    base_url=OPEN_ROUTER_BASE_URL,
    api_key=os.getenv("OPEN_ROUTER_API_KEY"),
)
"""Pydantic-AI OpenAI model configured for Open Router.

    This instance of the Pydantic-AI OpenAI model is configured to use the Open Router API.
"""

# Gemini Pydantic-AI model related constants - testing
GEMINI_MODEL_NAME = "gemini-2.0-flash-exp"
"""Name of the Gemini model.

    This string specifies the name of the Gemini model to be used.
"""
GEMINI_MODEL = GeminiModel(
    model_name=GEMINI_MODEL_NAME, api_key=os.getenv("GEMINI_API_KEY")
)
"""Pydantic-AI Gemini model.

   This instance of the Pydantic-AI Gemini model is configured with the API key.
"""

# Model used in project
PYDANTIC_AI_MODEL = GEMINI_MODEL
"""The Pydantic-AI model used in the project.

    This is the main model used for generating text responses.
"""

# YouTube API related constants
YOUTUBE_URL_REGEX = r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/[a-zA-Z0-9_\-]+"
"""Regex for matching YouTube URLs.

    This regular expression is used to validate YouTube URLs.
"""
ALLOWED_DOMAINS = ["youtube.com", "www.youtube.com", "youtu.be"]
"""Allowed domains for YouTube URLs.

    This list specifies the valid domains for YouTube URLs.
"""
YOUTUBE_API_ENDPOINT = "https://www.googleapis.com/youtube/v3/videos"
"""Endpoint for YouTube API videos.

    This string defines the API endpoint for retrieving video information from YouTube.
"""
YOUTUBE_LIVE_API_ENDPOINT = "https://www.googleapis.com/youtube/v3/liveChat/messages"
"""Endpoint for YouTube API live chat messages.

    This string defines the API endpoint for retrieving live chat messages from YouTube.
"""

# Supabase setup constants
SUPABASE_CLIENT = create_client(
    os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY")
)
"""Supabase client.

    This instance of the Supabase client is configured to interact with the Supabase database.
"""

# Table names
MESSAGES = "messages"
"""Name of the messages table.

    This string represents the name of the table storing chat messages.
"""
YT_KEYS = "youtube_keys"
"""Name of the youtube keys table.

    This string represents the name of the table storing youtube API keys.
"""
YT_STREAMS = "youtube_streams"
"""Name of the youtube streams table.

    This string represents the name of the table storing youtube stream information.
"""
YT_BUZZ = "youtube_buzz"
"""Name of the youtube buzz table.

    This string represents the name of the table storing youtube buzz information.
"""
YT_REPLY = "youtube_reply"
"""Name of the youtube reply table.

    This string represents the name of the table storing youtube reply information.
"""
STREAMER_KB = "streamer_knowledge"
"""Name of the streamer knowledge table.

    This string represents the name of the table storing streamer knowledge base.
"""
