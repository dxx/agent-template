"""Skills 技能中间件。支持 skills 系统"""
from collections.abc import Awaitable
from typing import Any, override, Callable
from langchain.tools import BaseTool
from langchain_core.tools import StructuredTool
from langchain.tools.tool_node import ToolCallRequest
from langchain.agents.middleware import (
    AgentMiddleware, ModelRequest, ModelResponse, AgentState
)
from langchain.messages import SystemMessage, AIMessage, ToolMessage
from langgraph.types import Command
from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ContextT,
    ResponseT,
    StateT,
)

from log import get_logger
from agent.skills import Skill, SkillLoader

logger = get_logger(__name__)

_LOAD_SKILL_TOOL_NAME = "load_skill"

_SKILLS_SYSTEM_PROMPT = """
## 技能系统
你可以访问技能去处理专业的问题

**可用的技能:**

{skills_list}

**何时使用技能:**
- 当需要更多详细信息去处理用户的问题
- 需要专业的知识或者结构化的流程
- 一个技能提供了复杂任务的处理方式

**如何使用技能:**
使用 `load_skill` 工具加载技能的详细描述，它会告诉你如何使用技能
1. 检查用户的提问是否符合技能的描述
2. 读取技能的全部指令，跟着技能的指令执行，`SKILL.md` 包含了一步一步的工作流程和案例
3. 访问需要的文件。技能可能包含了其他配置或参考文档，参考技能的 path 总是使用绝对路径读取
"""

class SkillsMiddleware(AgentMiddleware[StateT, ContextT, ResponseT]):
    """技能中间件。向系统提示词中注入技能描述"""

    def __init__(
            self,
            loader: SkillLoader,
            grouped_tools: dict[str, list[BaseTool]] | None = None
        ):
        """初始化 Skills 中间件并生成技能提示词。

        Args:
            loader: 技能加载器。负责加载技能、按名称获取技能和读取资源内容。
            grouped_tools: 按技能名称分组的工具列表。当模型加载某个 skill 后，
                中间件会把对应工具动态加入模型可用工具集合。
        """

        self._loader = loader

        self.tools = [
            # 注册加载技能的工具
            self._create_load_skill_tool(),
            self._create_read_file_tool()
        ]
        self._grouped_tools = grouped_tools or {}

    @override
    def wrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], ModelResponse[ResponseT]]
    ) -> ModelResponse[ResponseT]:

        skills = self._loader.list_skills()
        if not skills:
            return handler(request)
        
        override_request = self._build_overridden_request(
            request, skills, self._extract_loaded_skill_names(request.state)
        )
        return handler(override_request)
    
    @override
    async def awrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], Awaitable[ModelResponse[ResponseT]]]
    ) -> ModelResponse[ResponseT]:
        
        skills = self._loader.list_skills()
        if not skills:
            return await handler(request)
        
        override_request = self._build_overridden_request(
            request, skills, self._extract_loaded_skill_names(request.state)
        )
        return await handler(override_request)
    
    @override
    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command[Any]],
    ) -> ToolMessage | Command[Any]:
        override_request = self._build_overridden_tool_request(request)
        return handler(override_request)
    
    @override
    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
    ) -> ToolMessage | Command[Any]:
        override_request = self._build_overridden_tool_request(request)
        return await handler(override_request)

    def _build_overridden_request(
        self,
        request: ModelRequest[ContextT],
        skills: list[Skill],
        skill_names: list[str]
    ) -> ModelRequest[ContextT]:
        skills_prompt = self._build_skills_prompt(skills)
        # 添加到系统消息中
        new_content = list(request.system_message.content_blocks if request.system_message else []) + [
            {"type": "text", "text": "\n\n" + skills_prompt}
        ]

        new_tools = [*request.tools]

        skill_tools = self._load_skill_tools(skill_names)
        if len(skill_tools) > 0:
            # 添加 skill 需要的工具，动态加载的工具需要在 wrap_tool_call 指定执行
            new_tools.extend(skill_tools)

        new_system_message = SystemMessage(content_blocks=new_content)

        override_reqeust = request.override(
            # 修改系统提示词
            system_message=new_system_message,
            # 修改模型调用前要使用的工具
            tools=new_tools
        )
        return override_reqeust
    
    def _create_load_skill_tool(self) -> BaseTool:
        # 定义加载 SKills 函数
        def load_skill(skill_name: str) -> str:
            """加载技能的完整内容。当你需要知道详细描述怎样处理时使用。
            将提供全面的指导说明
            例如: load_skill("search")

            Args:
                skill_name: 要加载的 skill 名称，必须是可以用的技能列表中的名称
            """
            skill = self._loader.get_skill(skill_name)
            if skill:
                return f"{skill['content']}"
                 
            available_skills = ", ".join(s["name"] for s in self._loader.list_skills())
            return f"技能未找到, 可用的技能: {available_skills}"
        
        # 定义加载 SKills 函数
        async def aload_skill(skill_name: str) -> str:
            """加载技能的完整内容。当你需要知道详细描述怎样处理时使用。
            将提供全面的指导说明
            例如: load_skill("search")

            Args:
                skill_name: 要加载的 skill 名称，必须是可以用的技能列表中的名称
            """
            return load_skill(skill_name)
        
        # 创建工具函数
        return StructuredTool.from_function(
            name=_LOAD_SKILL_TOOL_NAME,
            func=load_skill,
            coroutine=aload_skill,
            parse_docstring=True
        )
    
    def _create_read_file_tool(self) -> BaseTool:
        def read_source_file(file_path: str) -> str:
            """读取资源文件内容。
            
            Args:
                file_path: 读取文件的绝对路径。必须是绝对路径，不能是相对路径
            """

            return self._loader.resolve_source_content(file_path)

        async def aread_source_file(file_path: str) -> str:
            """读取资源文件内容。
            
            Args:
                file_path: 读取文件的绝对路径。必须是绝对路径，不能是相对路径
            """

            return await self._loader.aresolve_source_content(file_path)

        # 创建工具函数
        return StructuredTool.from_function(
            name="read_source_file",
            func=read_source_file,
            coroutine=aread_source_file,
            parse_docstring=True
        )

    def _build_skills_prompt(self, skills: list[Skill]) -> str:
        skills_list = []
        for skill in skills:
            # path 指定 SKILL.md 的来源位置，当需要读取参考文件时，SKILL.md 中指定了相对路径，可以给 LLM 做参考
            skills_list.append(
                f"- **{skill['name']}**: {skill['description']}\npath: {skill['path']}"
            )

        return _SKILLS_SYSTEM_PROMPT.format(
            skills_list="\n".join(skills_list)
        )
    
    def _extract_loaded_skill_names(self, state: AgentState[Any]) -> list[str]:
        message_list = state["messages"]
        if not message_list:
            return []
        skill_names = []
        for message in message_list:
            if not isinstance(message, AIMessage) or not message.tool_calls:
                continue
            for tool_call in message.tool_calls:
                if tool_call["name"] != _LOAD_SKILL_TOOL_NAME:
                    continue
                skill_name = tool_call["args"].get("skill_name", "")
                if skill_name:
                    skill_names.append(skill_name)
        return skill_names
    
    def _load_skill_tools(self, skill_names: list[str]) -> list[BaseTool]:
        if not skill_names or not self._grouped_tools:
            return []
        skill_tools = []
        for name in skill_names:
            if name in self._grouped_tools:
                skill_tools.extend(self._grouped_tools[name])
        return skill_tools
                
    def _build_overridden_tool_request(self, request: ToolCallRequest) -> ToolCallRequest:
        override_request = request
        tool_name = request.tool_call["name"]
        for tools in self._grouped_tools.values():
            for tool in tools:
                if tool.name == tool_name:
                    # 工具没有在创建 agent 或者 middleware 时定义，tool=None
                    # 返回动态匹配的工具
                    return request.override(tool=tool)
        return override_request
