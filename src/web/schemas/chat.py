from pydantic import BaseModel, Field, model_validator
from enum import StrEnum
from typing import Literal

# 决策类型：approve=通过 reject=拒绝
DecisionType = Literal["approve", "reject"]

class RequestMsgTypeEnum(StrEnum):
    """请求消息类型

    NORMAL: 普通消息
    DECISION: 决策内容消息
    """
    NORMAL = "NORMAL"
    DECISION = "DECISION"

class ResponseMsgTypeEnum(StrEnum):
    """响应消息类型

    NORMAL: 普通消息
    PROCESS: 过程处理消息
    APPROVE: 审批消息
    ERROR: 错误消息
    """
    NORMAL = "NORMAL"
    PROCESS = "PROCESS"
    APPROVE = "APPROVE"
    ERROR = "ERROR"

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

class ChatRequest(BaseModel):
    """对话请求"""
    msg_type: RequestMsgTypeEnum = Field(
        default=RequestMsgTypeEnum.NORMAL,
        description="消息类型：可选 NORMAL、DECISION",
    )
    content: str = Field(
        default="",
        description="对话请求内容"
    )
    decision: Decision | None = Field(
        default=None,
        description="审批决策内容"
    )

    @model_validator(mode="after")
    def validate_content(self):
        if self.msg_type == RequestMsgTypeEnum.NORMAL and (not self.content or len(self.content.strip()) == 0):
            raise ValueError("消息内容不能为空或仅包含空白字符")
        elif self.msg_type == RequestMsgTypeEnum.DECISION and not self.decision:
            raise ValueError("审批决策内容不能为空")
        
        self.content = self.content.strip()
        return self

class ChatResponse[T](BaseModel):
    """对话响应"""
    msg_id: str
    msg_type: ResponseMsgTypeEnum = Field(
        default=ResponseMsgTypeEnum.NORMAL,
        description="消息类型：可选 NORMAL、PROCESS、APPROVE、ERROR"
    )
    content: T | None = Field(default=None, description="对话响应内容")
    approve: Approve | None = Field(default=None, description="审批内容")
    created: int
