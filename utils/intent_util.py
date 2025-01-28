import re

import torch
from sentence_transformers import util

from constants.constants import (CHAT_INTENT_EXAMPLES, NLP_MODEL,
                                 STREAMER_INTENT_EXAMPLES, YOUTUBE_URL_REGEX)
from constants.enums import ChatIntentEnum, StreamerIntentEnum

# Compute embeddings for streamer intent examples
streamer_intent_embeddings = {}
for intent, examples in STREAMER_INTENT_EXAMPLES.items():
    # Generate embeddings for all examples of the intent
    embeddings = NLP_MODEL.encode(
        examples, convert_to_tensor=True, batch_size=32, show_progress_bar=True
    )
    # Take the mean embedding for the intent
    streamer_intent_embeddings[intent] = torch.mean(embeddings, dim=0)
print("Streamer Intent Embeddings generated!!")

# Compute embeddings for chat intent examples
chat_intent_embeddings = {}
for intent, examples in CHAT_INTENT_EXAMPLES.items():
    # Generate embeddings for all examples of the intent
    embeddings = NLP_MODEL.encode(
        examples, convert_to_tensor=True, batch_size=32, show_progress_bar=True
    )
    # Take the mean embedding for the intent
    chat_intent_embeddings[intent] = torch.mean(embeddings, dim=0)
print("Chat Intent Embeddings generated!!")


def contains_valid_youtube_url(user_query):
    # Regex pattern for YouTube URLs
    return re.search(YOUTUBE_URL_REGEX, user_query) is not None


async def classify_streamer_intent(messages: list[str], query) -> StreamerIntentEnum:
    try:
        # Encode the messages separately
        previous_messages = " || ".join(messages)

        previous_embedding = NLP_MODEL.encode(previous_messages, convert_to_tensor=True)
        latest_embedding = NLP_MODEL.encode(query, convert_to_tensor=True)

        # Combine embeddings with weights (giving more weight to the latest message)
        combined_embedding = 0.3 * previous_embedding + 0.7 * latest_embedding

        # Compute cosine similarity with each intent
        similarities = {
            streamer_intent: util.cos_sim(combined_embedding, intent_embedding).item()
            for streamer_intent, intent_embedding in streamer_intent_embeddings.items()
        }

        # Find the intent with the highest similarity
        predicted_intent: str = max(similarities, key=similarities.get)
        # If the START_STREAM query doesn't have a valid YouTube URL, classify it as
        # UNKNOWN
        if predicted_intent == "START_STREAM" and not contains_valid_youtube_url(
                query
        ):
            predicted_intent = "UNKNOWN"
        return StreamerIntentEnum[predicted_intent.upper()]
    except Exception as e:
        print(f"Error classifying intent: {e}")
        return StreamerIntentEnum.UNKNOWN


async def classify_chat_intent(chat) -> ChatIntentEnum:
    try:
        # Encode the query
        chat_embedding = NLP_MODEL.encode(chat, convert_to_tensor=True)

        # Compute cosine similarity with each intent
        similarities = {
            chat_intent: util.cos_sim(chat_embedding, intent_embedding).item()
            for chat_intent, intent_embedding in chat_intent_embeddings.items()
        }

        # Find the intent with the highest similarity
        predicted_intent: str = max(similarities, key=similarities.get)
        return ChatIntentEnum[predicted_intent.upper()]
    except Exception as e:
        print(f"Error classifying chat intent: {e}")
        return ChatIntentEnum.UNKNOWN
