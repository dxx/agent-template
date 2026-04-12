"""Skills 技能中间件。支持 skills 系统"""
import re
import yaml
from typing import Any, TypedDict, override
from langchain.tools import BaseTool
from langchain_core.tools import StructuredTool
from langchain.tools.tool_node import ToolCallRequest
from langchain.agents.middleware import (
    AgentMiddleware, ModelRequest, ModelResponse, AgentState
)
from langchain.messages import SystemMessage, AIMessage, ToolMessage
from langgraph.types import Command
from typing import Callable
from pathlib import Path

from log import get_logger

logger = get_logger(__name__)

MAX_SKILL_NAME_LENGTH = 64
MAX_SKILL_DESCRIPTION_LENGTH = 1024

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

class Skill(TypedDict):
    """技能信息"""
    name: str
    description: str
    content: str
    path: str

class SkillsMiddleware(AgentMiddleware):
    """技能中间件。向系统提示词中注入技能描述"""

    def __init__(
            self, dirs: list[str],
            grouped_tools: dict[str, BaseTool] = {}
        ):
        """初始化和生成技能提示词

        self.skills: list[Skill] = [
            {
                "name": "greet",
                "description": "如何和用户打招呼",
                "content": "用户打招呼的时候说类似 '你好'、'hello', 直接礼貌的回复"
            }
        ]
    
        grouped_tools: 分组工具，用于动态加载工具。当使用了 skill 后匹配对应的工具然后传输给大模型
        """

        if not dirs:
            raise ValueError("dirs 不能为空")
        
        self.skills: list[Skill] = []
        for directory in dirs:
            self.skills.extend(self._read_skills(directory))

        if not self.skills:
            return
        
        self._build_skills_prompt()

        self.tools = [
            # 注册加载技能的工具
            self._create_load_skill_tool()
        ]
        self.grouped_tools = grouped_tools

    @override
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse]
    ) -> ModelResponse:

        if not self.skills:
            return handler(request)
        
        override_request = self._build_overridden_request(
            request, self._extract_loaded_skill_names(request.state)
        )
        return handler(override_request)
    
    @override
    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse]
    ) -> ModelResponse:
        
        if not self.skills:
            return await handler(request)
        
        override_request = self._build_overridden_request(
            request, self._extract_loaded_skill_names(request.state)
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
        handler: Callable[[ToolCallRequest], ToolMessage | Command[Any]],
    ) -> ToolMessage | Command[Any]:
        override_request = self._build_overridden_tool_request(request)
        return await handler(override_request)

    def _build_overridden_request(self, request: ModelRequest, skill_names: list[str]) -> ModelRequest:
        # 添加到系统消息中
        new_content = list(request.system_message.content_blocks if request.system_message else []) + [
            {"type": "text", "text": "\n\n" + self.skills_prompt}
        ]

        new_tools = [*request.tools]

        skill_tools = self._load_skill_tools(skill_names)
        if len(skill_tools) > 0:
            # 添加 skill 需要的工具，动态加载的工具需要在 wrap_tool_call 指定执行
            new_tools.extend(skill_tools)

        new_system_message = SystemMessage(content=new_content)

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
            for skill in self.skills:
                if skill["name"] == skill_name:
                    return f"{skill["content"]}"
                
            available_skills = ", ".join(s["name"] for s in self.skills)
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
    
    def _build_skills_prompt(self):
        skill_names = set()

        skills_list = []
        for skill in self.skills:
            if skill["name"] in skill_names:
                logger.warning("Skill name '%s' is repetitive, keep the old skill. Repetitive skills from '%s'",
                               skill["name"], skill["path"]
                )
                continue
            # path 指定 SKILL.md 的来源位置，当需要读取参考文件时，SKILL.md 中指定了相对路径，可以给 LLM 做参考
            skills_list.append(
                f"- **{skill["name"]}**: {skill["description"]}\npath: {skill["path"]}"
            )
            skill_names.add(skill["name"])

        self.skills_prompt = _SKILLS_SYSTEM_PROMPT.format(
            skills_list="\n".join(skills_list)
        )

    def _read_skills(self, directory) -> list[Skill]:
        if not directory:
            raise ValueError("directory 不能为空")
        
        skill_directory = _resolve_path(directory)

        skill_directory_path = Path(skill_directory)
        skills = []
        if not skill_directory_path.exists() or not skill_directory_path.is_dir():
            return skills

        for path in skill_directory_path.iterdir():
            if not path.is_dir():
                continue
            skill_path = path.joinpath("SKILL.md")
            if not skill_path.exists():
                continue
            skill = self._parse_skill(skill_path)
            if not skill:
                continue
            logger.info(f"Load skill name: {skill["name"]}, path: {skill["path"]}")
            skills.append(skill)

        return skills
    
    def _parse_skill(self, skill_file_path: Path) -> Skill | None:
        skill_content = skill_file_path.read_text(encoding="utf-8")
        if not skill_content:
            return None
        
        start_index = skill_content.find("---")
        if start_index < 0:
            return None
        end_index = skill_content.find("---", 3)
        if end_index < 0:
            return None
        frontmatter_str = skill_content[3:end_index].strip()
        frontmatter = yaml.safe_load(frontmatter_str)
        content = skill_content[end_index + 3:].strip()
        skill_name = frontmatter["name"]
        if len(skill_name) > MAX_SKILL_NAME_LENGTH:
            logger.warning("Skill name '%s' exceeds %s characters", skill_name, MAX_SKILL_NAME_LENGTH)
            return None
        skill_description = frontmatter["description"]
        if len(skill_description) > MAX_SKILL_DESCRIPTION_LENGTH:
            logger.warning("Skill description of name '%s' exceeds %s characters", skill_name, MAX_SKILL_NAME_LENGTH)
            return None
        return {
            "name": skill_name,
            "description": skill_description,
            "content": content,
            "path": str(skill_file_path)
        }
    
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
        if not skill_names or not self.grouped_tools:
            return []
        skill_tools = []
        for name in skill_names:
            if name in self.grouped_tools:
                skill_tools.extend(self.grouped_tools[name])
        return skill_tools
                
    def _build_overridden_tool_request(self, request: ToolCallRequest) -> ToolCallRequest:
        override_request = request
        tool_name = request.tool_call["name"]
        for tools in self.grouped_tools.values():
            for tool in tools:
                if tool.name == tool_name:
                    # 工具没有在创建 agent 或者 middleware 时定义，tool=None
                    # 返回动态匹配的工具
                    return request.override(tool=tool)
        return override_request

def _resolve_path(file_path: str) -> str:
    path = ""
    if file_path.startswith("/"):
        path = file_path
    elif re.search(r"^[a-zA-Z]+:", file_path):
        path = file_path
    else:
        script_dir = Path(__file__).resolve().parent
        path = str(script_dir) + "/" + file_path.removeprefix("./")
    return path
    