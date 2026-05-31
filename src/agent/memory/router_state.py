from pydantic import BaseModel, Field
from typing import Annotated, NotRequired, TypedDict

class AgentRouter(BaseModel):
    """代理路由"""

    query: str = Field(description="代理处理的输入内容")
    name: str = Field(description="代理名称")


class RouterResult(BaseModel):
    """根据用户的输入内容，路由到特定的代理"""

    routers: list[AgentRouter] = Field(
        default_factory=list,
        description="处理任务的子代理列表"
    )


class AgentOutput(TypedDict):
    """代理的输出"""

    source: str
    result: str

def add_results(a: list[AgentOutput], b: list[AgentOutput]) -> list[AgentOutput]:
    """并发更新 results 时处理多个值
    当新值为空时，清空
    当新值不为空时，添加到原内容中
    """
    if not b:
        return []
    return a + b

class RouterState(TypedDict):
    """路由状态"""

    query: str
    """用户输入"""

    routers: list[AgentRouter]
    """路由结果"""

    router: NotRequired[AgentRouter]
    """当前待执行的代理路由。内部调度字段"""

    # operator.add 状态更新方式为累加
    results: Annotated[list[AgentOutput], add_results]
    """代理处理结果"""

    final_result: str
    """汇总后的处理结果"""
