"""任务代理持有者

保存可调用的任务代理，供路由图注册和接口查询使用。
"""

from agent.middleware import TaskAgent


class TaskAgentHolder:
    """任务代理持有者

    按名称注册和查找任务代理。
    """

    def __init__(self) -> None:
        self._agents: dict[str, TaskAgent] = {}

    def register(self, agent: TaskAgent) -> None:
        """注册任务代理"""

        name = agent.get_name()
        if name in self._agents:
            raise ValueError(f"Duplicate agent: {name}")
        self._agents[name] = agent

    def get_agents(self) -> list[TaskAgent]:
        """获取全部任务代理"""

        return list(self._agents.values())

    def get_agent_names(self) -> list[str]:
        """获取全部任务代理名称"""

        return list(self._agents.keys())

    def get_agent(self, name: str) -> TaskAgent | None:
        """按名称获取任务代理"""

        return self._agents.get(name)


task_agent_holder = TaskAgentHolder()
