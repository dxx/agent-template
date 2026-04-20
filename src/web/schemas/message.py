from typing import Literal
from pydantic import BaseModel, Field

MessageType = Literal["user", "agent"]

class Message(BaseModel):
    """消息信息"""
    message_id: str = Field(default="", description="消息 ID")
    message_type: MessageType = Field(description="消息类型: user、agent")
    content: str = Field(description="消息内容")

class MessageResponse(BaseModel):
    """消息响应"""
    chat_id: str = Field(description="对话 ID")
    messages: list[Message] = Field(description="消息列表")
