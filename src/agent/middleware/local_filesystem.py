"""本地 Filesystem 中间件。动态注入文件系统工具。"""

import re
from collections.abc import Awaitable
from pathlib import Path
from typing import Any, Callable, override

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.agents.middleware.types import ContextT, ResponseT, StateT
from langchain.messages import SystemMessage
from langchain.tools import BaseTool, ToolRuntime
from langchain_core.tools import StructuredTool


_FILESYSTEM_SYSTEM_PROMPT = """
## 文件系统工具

你可以使用文件系统工具读取文件、写入文件、编辑文件和查看目录。

**路径要求:**
- 所有传给工具的文件路径必须以 `/` 开始。
- 不要使用相对路径，如 `./README.md`、`../README.md`。

**可用工具:**
- `ls`: 查看目录下有哪些文件和子目录。不确定路径时先使用这个工具。
- `read_file`: 读取文件内容，支持通过 `offset` 和 `limit` 按行号分页读取。读取大文件时不要一次性读取全部内容。
- `edit_file`: 编辑已有文件。修改已有文件时优先使用这个工具，并提供唯一匹配的 `old_text`。
- `write_file`: 写入文件。仅在创建新文件或需要完整覆盖文件时使用。

写入和编辑会修改文件，应谨慎操作。
"""

class FilesystemMiddleware(AgentMiddleware[StateT, ContextT, ResponseT]):
    """文件系统中间件。向模型动态注入文件系统工具和提示词。"""

    def __init__(
        self,
        work_dir: str | Path | None = None,
        isolate_by_user_id: bool = False,
    ):
        """初始化文件系统中间件。

        Args:
            work_dir: 文件系统工具的工作目录。所有路径操作都必须在该目录中。
                如果为 None，使用当前进程工作目录；如果传入路径不存在，也回退到当前进程工作目录。
            isolate_by_user_id: 是否使用 context 中的 user_id 隔离工作目录。启用后，每次文件操作都会以
                `work_dir / user_id` 作为实际工作目录；未启用时，实际工作目录就是 `work_dir`。
        """
        if work_dir is None:
            self.work_dir = Path.cwd().resolve()
        else:
            work_path = Path(work_dir)
            self.work_dir = work_path.resolve() if work_path.exists() else Path.cwd().resolve()
        self.isolate_by_user_id = isolate_by_user_id
        self.tools = self._create_tools()

    @override
    def wrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], ModelResponse[ResponseT]],
    ) -> ModelResponse[ResponseT]:
        override_request = self._build_overridden_request(request)
        return handler(override_request)

    @override
    async def awrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], Awaitable[ModelResponse[ResponseT]]],
    ) -> ModelResponse[ResponseT]:
        override_request = self._build_overridden_request(request)
        return await handler(override_request)

    def _build_overridden_request(
        self, request: ModelRequest[ContextT]
    ) -> ModelRequest[ContextT]:
        new_content = list(
            request.system_message.content_blocks if request.system_message else []
        ) + [{"type": "text", "text": "\n\n" + _FILESYSTEM_SYSTEM_PROMPT}]
        new_system_message = SystemMessage(content_blocks=new_content)
        return request.override(system_message=new_system_message)

    def _create_tools(self) -> list[BaseTool]:
        return [
            StructuredTool.from_function(
                name="ls",
                func=self._ls,
                coroutine=self._als,
                parse_docstring=True,
            ),
            StructuredTool.from_function(
                name="read_file",
                func=self._read_file,
                coroutine=self._aread_file,
                parse_docstring=True,
            ),
            StructuredTool.from_function(
                name="write_file",
                func=self._write_file,
                coroutine=self._awrite_file,
                parse_docstring=True,
            ),
            StructuredTool.from_function(
                name="edit_file",
                func=self._edit_file,
                coroutine=self._aedit_file,
                parse_docstring=True,
            ),
        ]

    def _resolve_path(
        self, key: str, runtime: ToolRuntime[Any, Any] | None = None
    ) -> Path:
        if not key:
            raise ValueError("路径不能为空")

        work_dir = self._get_work_dir(runtime)

        if re.match(r"^[a-zA-Z]:", str(work_dir)):
            new_key = key
            if re.match(r"^[a-zA-Z]:", key):
                new_key = key[2:].replace("\\", "/")
            resolved_path = (work_dir / new_key.removeprefix("/")).resolve()
        elif (path := Path(key)).is_absolute():
            resolved_path = (work_dir / str(path).removeprefix("/")).resolve()
        else:
            resolved_path = (work_dir / path).resolve()

        if resolved_path != work_dir and not resolved_path.is_relative_to(work_dir):
            raise ValueError(f"路径超出允许的工作目录: {key}")

        return resolved_path

    def _get_work_dir(self, runtime: ToolRuntime[Any, Any] | None = None) -> Path:
        if not self.isolate_by_user_id:
            return self.work_dir

        user_id = self._get_user_id(runtime)
        if not user_id:
            return self.work_dir

        work_dir = (self.work_dir / user_id).resolve()
        if work_dir != self.work_dir and not work_dir.is_relative_to(self.work_dir):
            raise ValueError(f"user_id 超出允许的工作目录: {user_id}")
        work_dir.mkdir(parents=True, exist_ok=True)
        return work_dir

    def _get_user_id(self, runtime: ToolRuntime[Any, Any] | None = None) -> str | None:
        if runtime is None:
            return None

        context = getattr(runtime, "context", None)
        if not context:
            return None

        user_id = getattr(context, "user_id", None)
        return str(user_id) if user_id else None

    def _ls(self, runtime: ToolRuntime[Any, Any], path: str = "/") -> str:
        """查看目录下有哪些文件和子目录。

        Args:
            path: 目录路径。必须是绝对路径，不能是相对路径
        """
        try:
            resolved_path = self._resolve_path(path, runtime)
            if not resolved_path.exists():
                return f"目录不存在: {path}"
            if not resolved_path.is_dir():
                return f"路径不是目录: {path}"

            entries = sorted(resolved_path.iterdir(), key=lambda item: item.name.lower())
            if not entries:
                return "目录为空"

            return "\n".join(
                f"[{'dir' if entry.is_dir() else 'file'}] {entry.name}"
                for entry in entries
            )
        except ValueError as exc:
            return str(exc)

    async def _als(
        self, runtime: ToolRuntime[Any, Any], path: str = "/"
    ) -> str:
        """查看目录下有哪些文件和子目录。

        Args:
            path: 目录路径
        """
        return self._ls(runtime, path)

    def _read_file(
        self,
        file_path: str,
        runtime: ToolRuntime[Any, Any],
        offset: int = 1,
        limit: int = 2000,
    ) -> str:
        """读取文件内容，支持按行号分页读取。

        Args:
            file_path: 读取文件的绝对路径。必须是绝对路径，不能是相对路径
            offset: 开始读取的行号，1 表示第一行
            limit: 最多读取的行数
        """
        if offset < 1:
            return "offset 必须大于等于 1"
        if limit < 1:
            return "limit 必须大于等于 1"

        try:
            path = self._resolve_path(file_path, runtime)
            if not path.exists():
                return f"文件不存在: {file_path}"
            if not path.is_file():
                return f"路径不是文件: {file_path}"

            lines = path.read_text(encoding="utf-8").splitlines()
            if not lines:
                return "文件为空"

            if offset > len(lines):
                return f"没有可读取的内容：offset 超出文件总行数，总行数为 {len(lines)}"

            selected_lines = lines[offset - 1 : offset - 1 + limit]
            return "\n".join(
                f"{line_number}: {line}"
                for line_number, line in enumerate(selected_lines, start=offset)
            )
        except ValueError as exc:
            return str(exc)

    async def _aread_file(
        self,
        file_path: str,
        runtime: ToolRuntime[Any, Any],
        offset: int = 1,
        limit: int = 2000,
    ) -> str:
        """读取文件内容，支持按行号分页读取。

        Args:
            file_path: 读取文件的绝对路径。必须是绝对路径，不能是相对路径
            offset: 开始读取的行号，1 表示第一行
            limit: 最多读取的行数
        """
        return self._read_file(file_path, runtime, offset, limit)

    def _write_file(
        self,
        file_path: str,
        content: str,
        runtime: ToolRuntime[Any, Any],
    ) -> str:
        """写入文件。

        Args:
            file_path: 文件路径
            content: 写入文件的内容
        """
        try:
            path = self._resolve_path(file_path, runtime)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return "写入文件成功"
        except ValueError as exc:
            return str(exc)

    async def _awrite_file(
        self,
        file_path: str,
        content: str,
        runtime: ToolRuntime[Any, Any],
    ) -> str:
        """写入文件。

        Args:
            file_path: 文件路径
            content: 写入文件的内容
        """
        return self._write_file(file_path, content, runtime)

    def _edit_file(
        self,
        file_path: str,
        old_text: str,
        new_text: str,
        runtime: ToolRuntime[Any, Any],
    ) -> str:
        """编辑文件内容。仅当旧文本唯一匹配时替换。

        Args:
            file_path: 文件路径
            old_text: 要替换的旧文本
            new_text: 替换后的新文本
        """
        if not old_text:
            return "old_text 不能为空"

        try:
            path = self._resolve_path(file_path, runtime)
            if not path.exists():
                return f"文件不存在: {file_path}"
            if not path.is_file():
                return f"路径不是文件: {file_path}"

            content = path.read_text(encoding="utf-8")
            match_count = content.count(old_text)
            if match_count == 0:
                return "未找到要替换的文本"
            if match_count > 1:
                return "要替换的文本匹配多次，请提供更精确的上下文"

            path.write_text(content.replace(old_text, new_text, 1), encoding="utf-8")
            return "编辑文件成功"
        except ValueError as exc:
            return str(exc)

    async def _aedit_file(
        self,
        file_path: str,
        old_text: str,
        new_text: str,
        runtime: ToolRuntime[Any, Any],
    ) -> str:
        """编辑文件内容。仅当旧文本唯一匹配时替换。

        Args:
            file_path: 文件路径
            old_text: 要替换的旧文本
            new_text: 替换后的新文本
        """
        return self._edit_file(file_path, old_text, new_text, runtime)
