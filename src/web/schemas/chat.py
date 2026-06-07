from datetime import datetime
from enum import StrEnum
from typing import Any, Literal, TypedDict
from pydantic import BaseModel, Field, model_validator


# 决策类型：approve=通过 reject=拒绝
DecisionType = Literal["approve", "reject"]


class RequestMsgTypeEnum(StrEnum):
    """请求消息类型

    NORMAL: 普通消息
    DECISION: 决策内容消息
    """

    NORMAL = "normal"
    DECISION = "decision"


class ResponseMsgTypeEnum(StrEnum):
    """响应消息类型

    NORMAL: 普通消息
    PROCESS: 过程处理消息
    APPROVE: 审批消息
    ERROR: 错误消息
    """

    NORMAL = "normal"
    PROCESS = "process"
    APPROVE = "approve"
    ERROR = "error"


class ApproveItem(BaseModel):
    """审批项信息"""

    name: str
    description: str
    decisions: list[DecisionType]


class Approve(BaseModel):
    """审批内容"""

    approve_id: str
    items: list[ApproveItem] = Field(description="审批项")


class DecisionItem(BaseModel):
    """审批决策项信息"""

    decision_type: DecisionType
    description: str = Field(default="", description="决策描述。可为空")


class Decision(BaseModel):
    """审批决策内容"""

    decision_id: str
    items: list[DecisionItem] = Field(description="决策项。和审批内容顺序对应")


class TextBlock(TypedDict):
    """文本内容"""
    type: Literal["text"]
    text: str


class ImageBlock(TypedDict):
    """OpenAI 兼容格式的图片内容

    示例:
        {"type": "image_url", "image_url": {"url": "demo.png"}}
        {"type": "image_url", "image_url": {"url": "demo.png", "detail": "high"}}
        {"type": "image_url", "image_url": {"url": "demo.png"}, "max_pixels": 16384 * 32 * 32}
    """
    type: Literal["image_url"]
    image_url: dict[str, Any]


class VideoBlock(TypedDict):
    """OpenAI 兼容格式的视频内容

    示例:
        {"type": "video_url","video_url": {"url":  "demo.mp4"}}
        {"type": "video_url","video_url": {"url":  "demo.mp4", "fps": 2}}
        {"type": "video_url","video_url": {"url":  "demo.mp4"}, "fps": 2}
    """
    type: Literal["video_url"]
    video_url: dict[str, Any]


Multimodal = TextBlock | ImageBlock | VideoBlock
"""多模态内容"""


class ChatRequest(BaseModel):
    """对话请求"""

    msg_type: RequestMsgTypeEnum = Field(
        default=RequestMsgTypeEnum.NORMAL,
        description="消息类型：可选 normal、decision",
    )
    content: str | list[Multimodal] | None = Field(default=None, description="对话请求内容")
    decision: Decision | None = Field(default=None, description="审批决策内容")

    @model_validator(mode="after")
    def validate_content(self):
        if self.msg_type == RequestMsgTypeEnum.NORMAL and (
            not self.content or (isinstance(self.content, str) and len(self.content.strip()) == 0)
        ):
            raise ValueError("消息内容不能为空或仅包含空白字符")
        elif self.msg_type == RequestMsgTypeEnum.DECISION and not self.decision:
            raise ValueError("审批决策内容不能为空")

        return self


class ChatResponse(BaseModel):
    """对话响应"""

    msg_id: str
    msg_type: ResponseMsgTypeEnum = Field(
        default=ResponseMsgTypeEnum.NORMAL,
        description="消息类型：可选 normal、process、approve、error",
    )
    content: str | None = Field(default=None, description="对话响应内容")
    approve: Approve | None = Field(default=None, description="审批内容")
    created: int | None = Field(default_factory=lambda: int(datetime.now().timestamp() * 1000), description="创建时间戳（毫秒）")
