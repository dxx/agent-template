from pydantic import BaseModel, Field
from typing import Annotated, NotRequired, TypedDict

class RouteTask(BaseModel):
    """路由任务：一条路由决策，包含目标代理与分配给它的任务内容"""

    query: str = Field(description="代理处理的任务内容")
    name: str = Field(description="代理名称")


class RouterResult(BaseModel):
    """根据用户的输入内容，路由到特定的代理"""

    routers: list[RouteTask] = Field(
        default_factory=list,
        description="处理任务的子代理列表"
    )


class AgentTask(TypedDict):
    """指定的任务代理及任务内容。

    由调用方解析用户输入后指定要调用的代理及各自的任务，
    路由时直接使用，跳过路由模型的路由判断。
    """

    name: str
    """代理名称"""

    query: str
    """分配给该代理的任务内容"""


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

    target_agents: NotRequired[list[AgentTask]]
    """指定的任务代理。

    非空时跳过路由模型的路由判断，直接调用指定代理。
    """

    routers: list[RouteTask]
    """路由结果。由 router 节点生成"""

    router: NotRequired[RouteTask]
    """当前待执行的代理路由。内部调度字段"""

    # operator.add 状态更新方式为累加
    results: Annotated[list[AgentOutput], add_results]
    """代理处理结果"""

    final_result: str
    """汇总后的处理结果"""
