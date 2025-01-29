from enum import Enum


class StreamerIntentEnum(Enum):
    """
    Enumeration representing the different intents a streamer might have.

    This enum defines the possible actions a streamer might want to perform,
    such as starting a stream, checking the current buzz, or replying to a post.
    """

    START_STREAM = 0
    """Indicates the streamer intends to start a new stream."""
    CURRENT_BUZZ = 1
    """Indicates the streamer intends to check the current buzz."""
    NEXT_BUZZ = 2
    """Indicates the streamer intends to check the next buzz."""
    POST_REPLY = 3
    """Indicates the streamer intends to reply to a post."""
    UNKNOWN = 4
    """Indicates the streamer's intent is unknown or could not be determined."""


class BuzzStatusEnum(Enum):
    """
    Enumeration representing the different statuses a buzz can have.

    This enum defines the various stages a buzz can be in, from being found to being
    active or inactive.
    """

    FOUND = 0
    """Indicates that the buzz has been initially found."""
    PROCESSING = 1
    """Indicates that the buzz is currently being processed."""
    ACTIVE = 2
    """Indicates that the buzz is currently active."""
    INACTIVE = 3
    """Indicates that the buzz is currently inactive."""


class StateEnum(Enum):
    """
    Enumeration representing a binary or pending state.

    This enum defines states that are typically represented as a simple yes/no,
    with an option for a pending state.
    """

    NO = 0
    """Indicates a negative or 'no' state."""
    YES = 1
    """Indicates a positive or 'yes' state."""
    PENDING = 2
    """Indicates a pending or undecided state."""


class ChatIntentEnum(Enum):
    """
    Enumeration representing the different intents a user might have in a chat.

    This enum defines the possible purposes behind a user's message in a chat,
    such as asking a question, expressing a concern, or making a request.
    """

    UNKNOWN = 0
    """Indicates the user's intent is unknown or could not be determined."""
    QUESTION = 1
    """Indicates the user is asking a question."""
    CONCERN = 2
    """Indicates the user is expressing a concern."""
    REQUEST = 3
    """Indicates the user is making a request."""
