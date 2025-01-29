import re
import time
from urllib.parse import parse_qs, urlparse

import requests
from cachetools.func import ttl_cache
from constants.constants import ALLOWED_DOMAINS, YOUTUBE_API_ENDPOINT
from constants.enums import BuzzStatusEnum
from exceptions.user_error import UserError
from utils import supabase_util


@ttl_cache(ttl=180)
async def get_youtube_api_keys():
    """
    Retrieves YouTube API keys from the Supabase database.

    This function uses a time-to-live (TTL) cache to store the API keys for 180 seconds,
    reducing the number of database calls.

    Returns:
        list: A list of dictionaries, where each dictionary contains an API key
              and its associated information.

    Raises:
        Exception: If there's an error retrieving the API keys from the database.
    """
    return await supabase_util.get_youtube_api_keys()


async def validate_and_extract_youtube_id(url: str) -> str:
    """
    Validates a YouTube URL and extracts the video ID if the URL is valid.

    This function parses the provided URL, checks if the domain is valid
    (either 'youtu.be' or 'youtube.com'), and extracts the 11-character
    alphanumeric video ID from the URL. It supports standard, shortened,
    and embed URL formats.

    Args:
        url (str): The YouTube URL to validate and parse.

    Returns:
        str: The extracted video ID if the URL is valid.

    Raises:
        UserError: If the provided URL is invalid due to an invalid domain,
                   invalid path, or invalid video ID format.
        Exception: If there's any other unexpected error during the process.
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
    Retrieves stream metadata for a given YouTube video ID using the YouTube API.

    This function takes a YouTube video ID, calls the YouTube API to get
    live streaming details and snippet information, and returns the API response.
    It uses a retry mechanism with multiple API keys if the initial request fails.

    Args:
        video_id (str): The YouTube video ID to fetch metadata for.

    Returns:
        dict: The JSON response from the YouTube API containing stream metadata.

    Raises:
        UserError: If there's an error related to the user input or API usage.
        Exception: If there's any other unexpected error during the process.
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

    This function iterates through a list of API keys, attempting to make a POST
    request to the specified URL. If a request fails, it retries with the next key
    after a short delay. The function handles both API key authentication and
    bearer token authentication based on the `use_keys` flag.

    Args:
        url (str): The URL to make the POST request to.
        params (dict): The parameters to include in the POST request.
        payload (dict): The payload to include in the POST request.
        api_keys (list): A list of dictionaries, where each dictionary contains
                        either an 'api_key' or an 'access_token' and other
                        associated information.
        use_keys (bool): If True, uses 'api_key' for authentication;
                        otherwise, uses 'access_token'.

    Returns:
        dict: The JSON response from the POST request if successful.

    Raises:
        Exception: If all API keys fail or the maximum number of retries is reached.
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
                f"Attempt {attempt + 1}: {response.status_code=}\nBody="
                f"{response.json()}. Retrying..."
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

    This function iterates through a list of API keys, attempting to make a GET
    request to the specified URL. If a request fails, it retries with the next key
    after a short delay. The function handles both API key authentication and
    bearer token authentication based on the `use_keys` flag.

    Args:
        url (str): The URL to make the GET request to.
        params (dict): The parameters to include in the GET request.
        api_keys (list): A list of dictionaries, where each dictionary contains
                        either an 'api_key' or an 'access_token' and other
                        associated information.
        use_keys (bool): If True, uses 'api_key' for authentication;
                        otherwise, uses 'access_token'.

    Returns:
        dict: The JSON response from the GET request if successful.

    Raises:
        Exception: If all API keys fail or the maximum number of retries is reached.
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
                f"Attempt {attempt + 1}: {response.status_code=}\nBody="
                f"{response.json()}. Retrying..."
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


async def deactivate_stream(session_id):
    """
    Deactivates all streams and marks all replies as inactive for a given session.

    This function uses the provided session ID to deactivate existing streams
    associated with the session and marks all replies as inactive. This is
    typically done when a new stream is being processed for the same session.

    Args:
        session_id (str): The session ID for which to mark streams as unavailable
                          and replies as inactive.

    Raises:
        Exception: If there is an error during the deactivation process.
    """
    try:
        await supabase_util.deactivate_existing_streams(session_id)
        await supabase_util.deactivate_replies(session_id)
    except Exception as e:
        print(f"Error>> deactivate_stream: {session_id=}\n{str(e)}")
        raise


async def deactivate_session(session_id):
    """
    Deactivates all streams and marks all buzz as inactive for a given session.

    This function deactivates streams associated with the session, and updates
    the buzz status to inactive for all buzz entries associated with the
    given session ID. This is typically used when a user prompts a new link
    in the session.

    Args:
        session_id (str): The session ID for which to deactivate streams and
                         mark buzz as inactive.

    Raises:
        Exception: If there is an error during the deactivation or update process.
    """
    try:
        await deactivate_stream(session_id)
        await supabase_util.update_buzz_status_by_session_id(
            session_id, BuzzStatusEnum.INACTIVE.value
        )
    except Exception as e:
        print(f"Error>> deactivate_session: {session_id=}\n{str(e)}")
        raise
