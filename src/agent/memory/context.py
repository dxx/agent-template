from dataclasses import dataclass

@dataclass
class AppAgentContext:
    """Agent 应用上下文"""

    user_id: str

    chat_id: str
    
    message_record: bool = True
    """是否把消息记录到聊天历史。False 时不记录。"""
