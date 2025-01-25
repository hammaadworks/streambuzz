import os

from dotenv import load_dotenv
from pydantic_ai.models.gemini import GeminiModel

load_dotenv()

START_STREAM_APPEND = "\n\nFetching buzz..."

MODEL = GeminiModel(
    model_name=os.getenv("MODEL_NAME"), api_key=os.getenv("GEMINI_API_KEY")
)
MODEL_RETRIES = 3
ALLOWED_DOMAINS = ["youtube.com", "www.youtube.com", "youtu.be"]
YOUTUBE_API_ENDPOINT = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_LIVE_API_ENDPOINT = "https://www.googleapis.com/youtube/v3/liveChat/messages"
