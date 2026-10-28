import uuid
from agent.memory.namespace import PREFIX

def generate_chat_id() -> str:
    """生成对话 ID"""
    return f"chat_{str(uuid.uuid4())}"

def format_thread_id(user_id: str, chat_id: str) -> str:
    """格式化线程 ID。使用 PREFIX 前缀隔离"""
    return f"{PREFIX}_{user_id}_{chat_id}"
