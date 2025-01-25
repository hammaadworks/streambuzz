import re
import time
from urllib.parse import urlparse, parse_qs

import requests
from cachetools.func import ttl_cache

from constants.constants import ALLOWED_DOMAINS, YOUTUBE_API_ENDPOINT
from exceptions.user_error import UserError
from utils import supabase_util


@ttl_cache(ttl=180)
async def get_youtube_api_keys():
    return await supabase_util.get_youtube_api_keys()


async def validate_and_extract_youtube_id(url: str) -> str:
    """
    Validates a YouTube URL and extracts the video ID if valid.

    Args:
        url (str): The YouTube URL to validate and parse.

    Returns:
        str: The extracted video ID if valid, otherwise raises ValueError.
    """
    try:
        # Parse the YouTube URL
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        path = parsed_url.path
        query = parse_qs(parsed_url.query)

        # Check if the domain is valid
        if domain not in ALLOWED_DOMAINS:
            raise UserError(f"Invalid YouTube domain: {domain}")

        # Extract video ID based on URL format
        if "youtu.be" in domain:
            # Shortened URL
            video_id = path[1:]  # Skip leading '/'
        elif "youtube.com" in domain:
            # Standard URL or embed URL
            if path == "/watch" and "v" in query:
                video_id = query["v"][0]
            elif path.startswith("/embed/"):
                video_id = path.split("/embed/")[1]
            else:
                raise UserError(f"Invalid YouTube video URL path: {path}")
        else:
            raise UserError("Unrecognized YouTube URL format.")

        # Validate video ID format (11-character alphanumeric)
        if not re.match(r"^[a-zA-Z0-9_-]{11}$", video_id):
            raise UserError(f"Invalid YouTube video ID: {video_id}")
        return video_id
    except UserError as ue:
        print(f"Error validating and extracting YouTube ID: {str(ue)}")
        raise
    except Exception as e:
        print(f"Error validating and extracting YouTube ID: {str(e)}")
        raise


async def get_stream_metadata(video_id: str):
    """
    This function extracts stream metadata from a YouTube video id.
    1. call yt api
    2. return error if invalid stream link
    3. store metadata associated with session id
    4. post metadata to messages table

    Args:
    - video_id (str): The YouTube video URL.
    """
    try:
        api_keys = await get_youtube_api_keys()
        params = {
            "part": "liveStreamingDetails,snippet",
            "id": video_id,
        }
        response = await get_request_with_retries(
            YOUTUBE_API_ENDPOINT, params, api_keys, use_keys=True
        )

        return response
    except UserError as ue:
        print(f"Error>> get_stream_metadata: {str(ue)}")
        raise
    except Exception as e:
        print(f"Error>> get_stream_metadata: {str(e)}")
        raise


async def post_request_with_retries(url, params, payload, api_keys, use_keys=False):
    """
    Makes a POST request with retries using multiple API keys.

    Args:
        url (str): The URL to make the POST request to.
        params (dict): The parameters to include in the POST request.
        payload (dict): The payload to include in the POST request.
        api_keys (list): A list of API keys to use for the request.
        use_keys (bool): Whether to use API keys in the request.

    Returns:
        dict: The JSON response from the POST request.

    Raises:
        Exception: If all API keys fail or maximum retries are reached.
    """
    for attempt, key_dict in enumerate(api_keys):
        if use_keys:
            params["key"] = key_dict["api_key"]
            response = requests.post(url, params=params, data=payload, timeout=10)
        else:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key_dict['access_token']}",
            }
            response = requests.post(
                url, headers=headers, params=params, data=payload, timeout=10
            )

        try:
            if response.status_code == 200:
                return response.json()

            # Log the failure
            print(
                f"Attempt {attempt + 1}: {response.status_code=}\nBody={response.json()}. Retrying..."
            )

        except requests.exceptions.RequestException as e:
            # Log the exception
            print(
                f"Error>> {str(e)}\nAttempt {attempt + 1}: {response.status_code=}\n"
                f"body={response.json()}. Retrying..."
            )

        # Retry after a short delay
        time.sleep(2)

    # If all attempts fail
    raise Exception("All API keys failed or maximum retries reached.")


async def get_request_with_retries(url, params, api_keys, use_keys=True):
    """
    Makes a GET request with retries using multiple API keys.

    Args:
        url (str): The URL to make the GET request to.
        params (dict): The parameters to include in the GET request.
        api_keys (list): A list of API keys to use for the request.
        use_keys (bool): Whether to use API keys in the request.

    Returns:
        dict: The JSON response from the GET request.

    Raises:
        Exception: If all API keys fail or maximum retries are reached.
    """
    for attempt, key_dict in enumerate(api_keys):
        if use_keys:
            params["key"] = key_dict["api_key"]
            response = requests.get(url, params=params, timeout=10)
        else:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key_dict['access_token']}",
            }
            response = requests.get(url, headers=headers, params=params, timeout=10)

        try:
            if response.status_code == 200:
                return response.json()

            # Log the failure
            print(
                f"Attempt {attempt + 1}: {response.status_code=}\nBody={response.json()}. Retrying..."
            )

        except requests.exceptions.RequestException as e:
            # Log the exception
            print(
                f"Error>> {str(e)}\nAttempt {attempt + 1}: {response.status_code=}\n"
                f"body={response.json()}. Retrying..."
            )

        # Retry after a short delay
        time.sleep(2)

    # If all attempts fail
    raise Exception("All API keys failed or maximum retries reached.")


async def deactivate_session(session_id):
    """
    Deactivates all streams and marks all buzz as read and written for a given session.
    Use:
    1. When user prompts a new link in the session
    """
    try:
        await mark_stream_unavailable(session_id)
        await supabase_util.mark_existing_buzz_read(session_id)
    except Exception as e:
        print(f"Error>> deactivate_session: {session_id=}\n{str(e)}")
        raise


async def mark_stream_unavailable(session_id):
    """
    Deactivates all streams and marks all buzz as written for a given session.

    Args:
        session_id (str): The session ID for which to mark streams as unavailable.

    Raises:
        Exception: If there is an error during the process.
    """
    try:
        await supabase_util.deactivate_existing_streams(session_id)
        await supabase_util.mark_existing_buzz_written(session_id)
    except Exception as e:
        print(f"Error>> mark_stream_unavailable: {session_id=}\n{str(e)}")
        raise
