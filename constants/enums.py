from enum import Enum


class StreamerIntentEnum(Enum):
    START_STREAM = 0
    CURRENT_BUZZ = 1
    NEXT_BUZZ = 2
    POST_REPLY = 3
    UNKNOWN = 4


class BuzzStatusEnum(Enum):
    FOUND = 0
    PROCESSING = 1
    ACTIVE = 2
    INACTIVE = 3
    
class StateEnum(Enum):
    NO = 0
    YES = 1
    PENDING = 2


class ChatIntentEnum(Enum):
    UNKNOWN = 0
    QUESTION = 1
    CONCERN = 2
    REQUEST = 3
