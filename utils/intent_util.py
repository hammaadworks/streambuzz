import re
from typing import List

import torch
from constants.constants import (CHAT_INTENT_EXAMPLES, CONFIDENCE_THRESHOLD, NLP_MODEL,
                                 STREAMER_INTENT_EXAMPLES, YOUTUBE_URL_REGEX)
from constants.enums import ChatIntentEnum, StreamerIntentEnum
from sentence_transformers import util

# Compute embeddings for streamer buzz_type examples
streamer_intent_embeddings = {}
for intent, examples in STREAMER_INTENT_EXAMPLES.items():
    # Generate embeddings for all examples of the buzz_type
    embeddings = NLP_MODEL.encode(
        examples, convert_to_tensor=True, batch_size=32, show_progress_bar=True
    )
    # Take the mean embedding for the buzz_type
    streamer_intent_embeddings[intent] = torch.mean(embeddings, dim=0)
print("Streamer Intent Embeddings generated!!")

# Compute embeddings for chat buzz_type examples
chat_intent_embeddings = {}
for intent, examples in CHAT_INTENT_EXAMPLES.items():
    # Generate embeddings for all examples of the buzz_type
    embeddings = NLP_MODEL.encode(
        examples, convert_to_tensor=True, batch_size=32, show_progress_bar=True
    )
    # Take the mean embedding for the buzz_type
    chat_intent_embeddings[intent] = torch.mean(embeddings, dim=0)
print("Chat Intent Embeddings generated!!")


def contains_valid_youtube_url(user_query: str) -> bool:
    """Checks if a given string contains a valid YouTube URL.

    This function uses a regular expression to determine if the input string
    matches the expected format of a YouTube URL.

    Args:
        user_query: The string to check for a YouTube URL.

    Returns:
        True if the string contains a valid YouTube URL, False otherwise.
    """
    return re.search(YOUTUBE_URL_REGEX, user_query) is not None


async def classify_streamer_intent(
    messages: List[str], query: str
) -> StreamerIntentEnum:
    """Classifies the intent of a streamer based on previous messages and the latest query.

    This function leverages sentence embeddings to determine the streamer's intent.
    It combines the embeddings of previous messages and the latest query, giving
    more weight to the latest query. Then, it calculates the cosine similarity
    between the combined embedding and pre-computed embeddings for each streamer
    intent. The intent with the highest similarity is returned.

    If the predicted intent is "START_STREAM" but the query does not contain a
    valid YouTube URL, the intent is classified as "UNKNOWN". This prevents
    incorrect classification when a user intends something else but uses similar
    wording.

    Args:
        messages: A list of previous messages from the user.
        query: The latest message from the user.

    Returns:
        The predicted streamer intent as a `StreamerIntentEnum` value.
        Returns `StreamerIntentEnum.UNKNOWN` if an error occurs during classification.
    """
    try:
        # Encode the messages separately
        previous_messages = " || ".join(messages)

        previous_embedding = NLP_MODEL.encode(previous_messages, convert_to_tensor=True)
        latest_embedding = NLP_MODEL.encode(query, convert_to_tensor=True)

        # Combine embeddings with weights (giving more weight to the latest message)
        combined_embedding = 0.3 * previous_embedding + 0.7 * latest_embedding

        # Compute cosine similarity with each buzz_type
        similarities = {
            streamer_intent: util.cos_sim(combined_embedding, intent_embedding).item()
            for streamer_intent, intent_embedding in streamer_intent_embeddings.items()
        }

        # Find the intent with the highest similarity score
        predicted_intent, max_similarity = max(similarities.items(), key=lambda x: x[1])

        # If confidence is too low, classify as UNKNOWN
        if max_similarity < CONFIDENCE_THRESHOLD:
            predicted_intent = StreamerIntentEnum.UNKNOWN

        # If the START_STREAM query doesn't have a valid YouTube URL, classify it as
        # UNKNOWN
        if predicted_intent == "START_STREAM" and not contains_valid_youtube_url(query):
            predicted_intent = "UNKNOWN"
        return StreamerIntentEnum[predicted_intent.upper()]
    except Exception as e:
        print(f"Error classifying buzz_type: {e}")
        return StreamerIntentEnum.UNKNOWN


async def classify_chat_intent(chat: str) -> ChatIntentEnum:
    """Classifies the intent of a chat message.

    This function uses sentence embeddings to classify the intent of a given chat
    message. It calculates the cosine similarity between the embedding of the chat
    message and pre-computed embeddings for each chat intent. The intent with the
    highest similarity is returned.

    Args:
        chat: The chat message to classify.

    Returns:
        The predicted chat intent as a `ChatIntentEnum` value.
        Returns `ChatIntentEnum.UNKNOWN` if an error occurs during classification.
    """
    try:
        # Encode the query
        chat_embedding = NLP_MODEL.encode(chat, convert_to_tensor=True)

        # Compute cosine similarity with each buzz_type
        similarities = {
            chat_intent: util.cos_sim(chat_embedding, intent_embedding).item()
            for chat_intent, intent_embedding in chat_intent_embeddings.items()
        }

        # Find the intent with the highest similarity score
        predicted_intent, max_similarity = max(similarities.items(), key=lambda x: x[1])

        # If confidence is too low, classify as UNKNOWN
        if max_similarity < CONFIDENCE_THRESHOLD:
            return ChatIntentEnum.UNKNOWN
        return ChatIntentEnum[predicted_intent.upper()]
    except Exception as e:
        print(f"Error classifying chat buzz_type: {e}")
        return ChatIntentEnum.UNKNOWN
