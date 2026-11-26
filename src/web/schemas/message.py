from typing import Literal
from pydantic import BaseModel, Field, model_validator


MessageType = Literal["user", "agent"]


class Message(BaseModel):
    """消息信息"""

    message_id: str = Field(default="", description="消息 ID")
    message_type: MessageType = Field(description="消息类型: user、agent")
    content: str = Field(description="消息内容")
    created: int = Field(description="创建时间戳（毫秒）")


class MessageResponse(BaseModel):
    """消息响应"""

    chat_id: str = Field(description="对话 ID")
    title: str | None = Field(default=None, description="会话标题。可选，未生成时为空")
    messages: list[Message] = Field(description="消息列表")


class GenerateTitleRequest(BaseModel):
    """生成会话标题请求"""

    content: str = Field(description="用于生成标题的用户输入内容")
    chat_id: str | None = Field(
        default=None,
        description="对话 ID。传入时生成成功后更新该对话标题；不传只返回标题",
    )

    @model_validator(mode="after")
    def validate_content(self):
        if not self.content or len(self.content.strip()) == 0:
            raise ValueError("内容不能为空或仅包含空白字符")
        self.content = self.content.strip()
        return self


class GenerateTitleResponse(BaseModel):
    """生成会话标题响应"""

    title: str = Field(description="生成的会话标题")
