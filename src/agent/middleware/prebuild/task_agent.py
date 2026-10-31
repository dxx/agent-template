"""任务代理基类。

`代理包装类，持有代理名称、描述和实际执行任务的 Runnable。

`TaskAgent` 的 `agent` 参数需要支持 `context` 参数，常见的几种：

- LangGraph 编译后的 `CompiledStateGraph`
- LangGraph `Pregel` 实例
- LangChain `create_agent` 创建的 agent
"""

from typing import Any

from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.types import Command


class TaskAgent:
    """任务代理基类。

    包装一个可执行的任务代理，提供名称、描述和统一的调用入口。

    Attributes:
        name: 代理名称。供调度方（如 task / route 工具）选择代理使用。
        description: 代理描述。说明该代理适合处理什么任务，供模型判断是否调用。
    """

    def __init__(
        self,
        *,
        name: str,
        description: str,
        agent: Runnable[Any, Any]
    ):
        """初始化任务代理。

        Args:
            name: 代理名称。
            description: 代理描述。
            agent: 实际执行任务的代理。必须支持 `context` 参数，通常是：

                - LangGraph 编译后的 `CompiledStateGraph`
                - LangGraph `Pregel` 实例
                - LangChain `create_agent` 创建的 agent
        """
        self.name = name
        self.description = description
        self._agent = agent

    def get_name(self) -> str:
        return self.name

    def get_description(self) -> str:
        return self.description

    def get_agent(self) -> Runnable[Any, Any]:
        return self._agent

    def invoke(
        self,
        input: dict[str, Any] | Command[Any] | None,
        config: RunnableConfig | None = None,
        *,
        context: Any | None = None,
        **kwargs: Any,
    ) -> dict[str, Any] | Any:
        return self._agent.invoke(
            input,
            config=config,
            context=context,
            **kwargs,
        )

    async def ainvoke(
        self,
        input: dict[str, Any] | Command[Any] | None,
        config: RunnableConfig | None = None,
        *,
        context: Any | None = None,
        **kwargs: Any,
    ) -> dict[str, Any] | Any:
        return await self._agent.ainvoke(
            input,
            config=config,
            context=context,
            **kwargs,
        )
