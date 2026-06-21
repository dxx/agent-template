# Sub Agents 子代理

子代理用于将复杂任务拆分给专门的 Agent 处理。主 Agent 通过 `SubAgentMiddleware` 获得一个 `task` 工具，并使用该工具按名称调用具体子代理。

## 工作方式

主 Agent 创建时会注册多个子代理：

```python
sub_agents = [
    FileManagerAgent(),
    ReseachAgent(),
    WritingAgent(),
    ReviewAgent(),
    GreetAgent(),
    UserAgent(),
]

create_agent(
    name="main_agent",
    middleware=[
        SubAgentMiddleware(sub_agents=sub_agents),
        ...
    ],
)
```

`SubAgentMiddleware` 会完成两件事：

- 注册 `task` 工具，供主 Agent 调用子代理
- 向系统提示词追加子代理使用说明，引导主 Agent 在合适场景委派任务

## 调用流程

1. 用户向主 Agent 发起请求
2. 主 Agent 判断任务是否适合委派给子代理
3. 主 Agent 调用 `task` 工具，传入 `agent_name` 和 `task_input`
4. `task` 工具根据 `agent_name` 找到对应 `SubAgent`
5. 中间件使用 `task_input` 构造新的子代理输入状态
6. 子代理独立执行任务，并返回自己的最终状态
7. 中间件提取子代理最后一条消息，作为 `ToolMessage` 返回给主 Agent
8. 主 Agent 根据子代理结果继续推理，并向用户输出最终回复

## task 工具

`task` 工具由 `SubAgentMiddleware` 自动创建，工具名固定为 `task`。

```python
task(
    agent_name: str,
    task_input: str,
    runtime: ToolRuntime,
) -> Command
```

参数说明：

| 参数 | 说明 |
| --- | --- |
| `agent_name` | 子代理名称，必须是已注册子代理的名称。 |
| `task_input` | 要交给子代理执行的任务内容，需要包含必要上下文。 |
| `runtime` | LangChain 工具运行时对象，由框架注入。 |

工具返回 `Command`，用于更新主 Agent 状态，并追加一条 `ToolMessage`。

## 适合使用子代理的场景

适合委派给子代理的任务：

- 任务复杂且包含多个步骤
- 任务可以独立完成，不依赖主 Agent 的中间推理过程
- 只需要子代理返回最终结果，不需要暴露子代理执行过程
- 多个任务相互独立，可以并行委派给多个子代理

不适合委派给子代理的任务：

- 简单问答或单步任务
- 需要主 Agent 持续参与每一步判断的任务
- 必须把中间过程直接展示给用户的任务

## SubAgent 基类

所有子代理都通过 `SubAgent` 包装。

```python
class SubAgent:
    def __init__(self, *, name: str, description: str, agent: Runnable[Any, Any]): ...
    def get_name(self) -> str: ...
    def get_description(self) -> str: ...
    def invoke(...): ...
    async def ainvoke(...): ...
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| `name` | 子代理名称，用于 `task.agent_name` 调度。 |
| `description` | 子代理能力描述，会出现在 `task` 工具描述中，帮助主 Agent 选择代理。 |
| `agent` | 实际执行任务的 LangChain Runnable，通常由 `create_agent` 创建。 |

注册子代理时，如果出现重复名称，会抛出异常：

```python
raise ValueError(f"Duplicate agent: {name}")
```

## 内置子代理

当前主 Agent 默认注册以下子代理：

| 子代理 | 名称 | 说明 |
| --- | --- | --- |
| `FileManagerAgent` | `file_manager` | 擅长对文件进行管理。 |
| `ReseachAgent` | `research` | 擅长从多个信息源收集和整理信息。 |
| `WritingAgent` | `writing` | 擅长根据需求撰写高质量内容。 |
| `ReviewAgent` | `review` | 擅长检查和改进内容质量，对事物进行评价。 |
| `GreetAgent` | `greet` | 擅长和用户打招呼。 |
| `UserAgent` | `user` | 负责用户信息管理。 |

## 状态传递

调用子代理前，中间件会基于主 Agent 当前状态构造新的输入状态：

```python
state = {k: v for k, v in runtime.state.items() if k not in _EXCLUDED_STATE_KEYS}
state["messages"] = [{"role": "user", "content": task_input}]
```

默认排除的状态字段：

```python
_EXCLUDED_STATE_KEYS = {"messages", "structured_response"}
```

这意味着：

- 主 Agent 的历史 `messages` 不会直接传给子代理
- 子代理会收到一条新的用户消息，内容是 `task_input`
- 除 `messages` 和 `structured_response` 外，其他状态字段会传递给子代理
- 如果子代理需要访问自定义状态，需要在子代理 `create_agent` 中配置对应 `state_schema`

## 上下文传递

调用子代理时会传递当前运行时上下文：

```python
result = await agent.ainvoke(
    inputs,
    context=runtime.context,
)
```

项目中通常使用 `AppAgentContext` 作为上下文结构，用于传递 `user_id`、`chat_id` 等请求级信息。

如果子代理需要访问上下文，需要在 `create_agent` 中配置：

```python
create_agent(
    context_schema=AppAgentContext,
    ...
)
```

## 返回结果

子代理必须返回包含 `messages` 字段的状态。

中间件会读取最后一条消息：

```python
message_text = result["messages"][-1].text.rstrip()
```

然后将该文本包装为 `ToolMessage` 返回给主 Agent：

```python
ToolMessage(
    name="task",
    content=message_text,
    tool_call_id=runtime.tool_call_id,
)
```

如果子代理返回结果中没有 `messages`，会抛出异常。

## sub_agent_calls

项目中定义了子代理调用记录字段：

```python
SUB_AGENT_CALLS_KEY = "sub_agent_calls"
```

当主 Agent 状态中存在 `sub_agent_calls` 字段时，`task` 工具会追加本次调用的子代理名称：

```python
state_update["sub_agent_calls"] = [*sub_agent_calls, agent_name]
```

主 Agent 初始化状态中包含：

```python
AppAgentState(sub_agent_calls=[])
```

该字段可用于记录一次对话中实际委派过哪些子代理。

## 示例：文件管理子代理

`FileManagerAgent` 使用文件系统中间件，并对读写文件操作启用人工审批。

```python
class FileManagerAgent(SubAgent):
    def __init__(self):
        agent = create_agent(
            model=create_chat_model(enable_thinking=False),
            name=SubAgentEnum.FILE_MANAGER.value,
            system_prompt=AGENT_FILE_MANAGER_PROMPT,
            context_schema=AppAgentContext,
            middleware=[
                FilesystemMiddleware(isolate_by_user_id=True),
                HumanInTheLoopMiddleware(
                    interrupt_on={
                        "write_file": {...},
                        "read_file": {...},
                    }
                ),
            ],
        )

        super().__init__(
            name=SubAgentEnum.FILE_MANAGER.value,
            description="擅长对文件进行管理",
            agent=agent,
        )
```

特点：

- 通过 `FilesystemMiddleware` 提供文件读写工具
- 使用 `isolate_by_user_id=True` 按用户隔离文件访问范围
- 使用 `HumanInTheLoopMiddleware` 对 `read_file` 和 `write_file` 触发审批

## 示例：研究子代理

`ReseachAgent` 使用 MCP 中间件接入 ArXiv 搜索服务。

```python
class ReseachAgent(SubAgent):
    def __init__(self):
        agent = create_agent(
            model=create_chat_model(),
            name=SubAgentEnum.RESEARCH.value,
            system_prompt=AGENT_RESEARCH_PROMPT,
            context_schema=AppAgentContext,
            middleware=[
                MCPClientMiddleware(
                    mcp_config={
                        "arxiv": {
                            "transport": "stdio",
                            "command": "uvx",
                            "args": [
                                "--from",
                                "arxiv-mcp-server==0.4.12",
                                "arxiv-mcp-server",
                                "--storage-path",
                                f"{Path.cwd()}/arxiv/paper",
                            ],
                        }
                    }
                )
            ],
        )
```

特点：

- 子代理可以有自己的工具和中间件
- MCP 能力只暴露给该子代理，不需要直接暴露给主 Agent

## 示例：技能子代理

`GreetAgent` 使用 `SkillsMiddleware` 加载技能，并根据技能动态启用工具。

```python
class GreetAgent(SubAgent):
    def __init__(self):
        agent = create_agent(
            model=create_chat_model(enable_thinking=False),
            name="greet",
            system_prompt="你是一个专业的招待助手，擅长和用户打招呼。",
            context_schema=AppAgentContext,
            state_schema=AppAgentState,
            middleware=[
                SkillsMiddleware(
                    loader=DirectorySkillLoader([str(skill_dir)]),
                    grouped_tools={
                        "greet": [greet]
                    },
                )
            ],
        )
```

特点：

- 子代理可以独立安装 Skills 能力
- 需要访问状态时，要配置 `state_schema=AppAgentState`

## 新增子代理

新增子代理通常需要 4 步。

### 1. 创建子代理类

在 `src/agent/subagents/` 下新增文件，例如 `translate.py`：

```python
from langchain.agents import create_agent

from agent.llm import create_chat_model
from agent.memory import AppAgentContext
from agent.middleware import SubAgent


class TranslateAgent(SubAgent):
    def __init__(self):
        agent = create_agent(
            model=create_chat_model(),
            name="translate",
            system_prompt="你是一个专业翻译助手，擅长在不同语言之间准确翻译。",
            context_schema=AppAgentContext,
        )

        super().__init__(
            name="translate",
            description="擅长翻译和润色多语言内容",
            agent=agent,
        )
```

### 2. 注册名称

如果希望统一管理名称，可以在 `src/agent/subagents/agent_enum.py` 中添加枚举：

```python
class SubAgentEnum(StrEnum):
    TRANSLATE = "translate"
```

也可以像 `GreetAgent` 和 `UserAgent` 一样直接使用字符串名称。

### 3. 注册到主 Agent

在 `src/agent/subagents/main.py` 中导入并加入 `sub_agents` 列表：

```python
from agent.subagents.translate import TranslateAgent

sub_agents = [
    FileManagerAgent(),
    ReseachAgent(),
    WritingAgent(),
    ReviewAgent(),
    GreetAgent(),
    UserAgent(),
    TranslateAgent(),
]
```

### 4. 调整描述

确保 `description` 简短清晰，因为主 Agent 会根据描述决定是否调用该子代理。

```python
description="擅长翻译和润色多语言内容"
```

## 设计建议

- 子代理名称保持简短稳定，避免频繁变更
- 子代理描述要说明能力边界，不要写得过于宽泛
- 子代理的工具和中间件只放它真正需要的能力
- 复杂能力优先放到专门子代理中，避免主 Agent 工具过多
- 需要访问 `state` 时配置 `state_schema`
- 需要访问请求上下文时配置 `context_schema`
- 子代理返回内容应面向主 Agent 汇总，不一定直接面向最终用户

## 注意事项

- `SubAgentMiddleware` 初始化时 `sub_agents` 不能为空，否则会抛出异常
- 子代理必须返回包含 `messages` 的状态，否则中间件无法提取结果
- 主 Agent 的历史消息不会完整传给子代理，必要上下文应写入 `task_input`
- 子代理中断、审批、工具调用等能力由子代理自身中间件决定
- 子代理的中间执行过程默认不会直接展示给用户，主 Agent 只看到 `task` 工具返回的文本结果
