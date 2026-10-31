from enum import StrEnum

class SubAgentEnum(StrEnum):
    """子代理名称枚举类"""

    FILE_MANAGER = "file_manager"
    RESEARCH = "research"
    WRITING = "writing"
    REVIEW = "review"
    GREETING = "greeting"
    USER = "user"
