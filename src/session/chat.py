import uuid

def generate_chat_id() -> str:
    """生成对话 ID"""
    return f"chat_{str(uuid.uuid4())}"

def format_thread_id(user_id: str, chat_id: str) -> str:
    """格式化线程 ID"""
    return f"{user_id}_{chat_id}"
