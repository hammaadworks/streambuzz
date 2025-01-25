from enum import Enum


class YoutubeKeyTypeEnum(Enum):
    READ = 0
    WRITE = 1


class StreamerIntentEnum(Enum):
    START_STREAM_STREAMER_INTENT = 0
    GET_CURRENT_BUZZ_STREAMER_INTENT = 1
    GET_NEXT_BUZZ_STREAMER_INTENT = 2
    REPLY_TO_BUZZ_STREAMER_INTENT = 3
    UNKNOWN_STREAMER_INTENT = 4


class ChatIntentEnum(Enum):
    QUESTION_CHAT = "Question"
    CONCERN_CHAT = "Concern"
    REQUEST_CHAT = "Request"
    UNKNOWN_CHAT = "Unknown"

class BuzzStatusEnum(Enum):
    FOUND = 0
    READ = 1
    ACTED = 2