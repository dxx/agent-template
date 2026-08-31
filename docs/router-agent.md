# Router Agent 路由代理

路由代理用于把用户请求交给内部路由图处理。主 Agent 通过 `RouteAgentMiddleware` 获得一个 `route` 工具，调用后由内部 `StateGraph` 自动选择一个或多个任务代理执行，并把结果合并成单个回答。

## 工作方式

路由代理由两层组成：

- 主 Agent：对外接收用户请求，并通过 `route` 工具触发路由处理
- 内部路由图：执行 `router -> call_agent -> join` 流程，负责选择代理、调用代理和合并结果

项目中通过 `create_router_agent` 创建路由编排 Agent：

```python
def create_router_agent() -> CompiledStateGraph[AgentState, AppAgentContext, Any, Any]:
    agents = [
        WritingAgent(),
        ResearchAgent(),
        ReviewAgent(),
        GreetAgent(),
        FileManagerAgent(),
    ]

    route_agent_middleware = RouteAgentMiddleware(
        name="router_agent",
        router_model=create_chat_model(enable_thinking=False),
        agents=agents,
        context_schema=AppAgentContext,
    )

    return create_agent(
        name="router_main_agent",
        model=create_chat_model(enable_thinking=False),
        context_schema=AppAgentContext,
        middleware=[
            route_agent_middleware,
            ...
        ],
    )
```

## RouteAgentMiddleware

`RouteAgentMiddleware` 是主 Agent 和内部路由图之间的连接层。

它会完成两件事：

- 注册 `route` 工具，供主 Agent 调用
- 向主 Agent 系统提示词追加路由工具使用说明

初始化参数：

| 参数 | 说明 |
| --- | --- |
| `name` | 内部路由图名称。 |
| `agents` | 可被路由调用的任务代理列表。 |
| `router_model` | 用于生成结构化路由结果的模型。 |
| `merge_model` | 用于合并多个任务代理结果的模型，不传时复用 `router_model`。 |
| `state_schema` | 内部 `StateGraph` 使用的状态结构，默认是 `RouterState`。 |
| `context_schema` | 内部 `StateGraph` 的上下文结构。 |
| `system_prompt` | 注入主 Agent 的路由工具使用说明，传入 `None` 时不注入。 |
| `router_prompt` | 路由模型使用的提示词。 |
| `tool_name` | 注册到主 Agent 的工具名称，默认是 `route`。 |

## route 工具

`route` 工具由 `RouteAgentMiddleware` 自动创建。

```python
route(runtime: ToolRuntime[Any, AgentState]) -> str
```

工具调用时不会要求模型显式传入用户问题，而是从当前主 Agent 状态中提取最近一条用户消息：

```python
def _build_router_input(state: AgentState) -> dict[str, Any]:
    query = _extract_user_input(state)
    return {
        "query": query,
    }
```

支持的消息形式：

- `HumanMessage`
- `{"role": "user", "content": "..."}`

如果没有找到用户消息，`query` 会是空字符串。

## 内部路由图

内部路由图由 `_RouteGraphAgent` 创建，使用 LangGraph `StateGraph` 编排。

```text
START -> router -> call_agent -> join -> END
```

节点说明：

| 节点 | 说明 |
| --- | --- |
| `router` | 使用 `router_model` 根据用户请求生成结构化路由结果。 |
| `call_agent` | 根据路由结果调用一个或多个任务代理。 |
| `join` | 合并任务代理结果，生成最终 `final_result`。 |

当 `router` 返回多个路由目标时，图会通过 `Send` 将任务分发给多个 `call_agent` 分支执行。

## RouterState

内部路由图使用 `RouterState` 管理状态。

```python
class RouterState(TypedDict):
    query: str
    routers: list[AgentRouter]
    router: NotRequired[AgentRouter]
    results: Annotated[list[AgentOutput], add_results]
    final_result: str
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| `query` | 原始用户输入。 |
| `routers` | 路由模型输出的任务代理列表。 |
| `router` | 当前分支正在执行的路由信息，属于内部调度字段。 |
| `results` | 多个任务代理的输出结果。 |
| `final_result` | 最终合并后的结果。 |

`results` 使用自定义 reducer `add_results`，用于合并多个并发分支的输出。当传入空列表时会清空结果。

## 路由结果结构

路由模型需要输出结构化结果 `RouterResult`。

```python
class AgentRouter(BaseModel):
    query: str = Field(description="代理处理的输入内容")
    name: str = Field(description="代理名称")


class RouterResult(BaseModel):
    routers: list[AgentRouter] = Field(default_factory=list)
```

示例：

```json
{
  "routers": [
    {
      "name": "research",
      "query": "调研 LangGraph StateGraph 的路由编排机制，并总结关键点"
    },
    {
      "name": "writing",
      "query": "根据调研内容撰写一份中文说明文档"
    }
  ]
}
```

路由规则：

- 只能选择已注册任务代理的 `name`
- 一个请求可以拆分给多个任务代理
- 每个 `router.query` 都应该是完整、独立的任务描述
- 如果没有合适代理，返回空列表：`{"routers": []}`
- 不在注册表中的代理名称会被过滤

## RouteTaskAgent

所有路由任务代理都通过 `RouteTaskAgent` 包装。

```python
class RouteTaskAgent:
    def __init__(self, *, name: str, description: str, agent: Runnable[Any, Any]): ...
    def get_name(self) -> str: ...
    def get_description(self) -> str: ...
    def invoke(...): ...
    async def ainvoke(...): ...
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| `name` | 任务代理名称，供路由模型选择。 |
| `description` | 任务代理能力描述，会出现在路由提示词中。 |
| `agent` | 实际执行任务的 LangChain Runnable，通常由 `create_agent` 创建。 |

注册任务代理时，如果出现重复名称，会抛出异常：

```python
raise ValueError(f"Duplicate agent: {name}")
```

## 内置任务代理

当前路由 Agent 默认注册以下任务代理：

| 任务代理 | 名称 | 说明 |
| --- | --- | --- |
| `WritingAgent` | `writing` | 擅长根据需求撰写高质量内容。 |
| `ResearchAgent` | `research` | 擅长从多个信息源收集和整理信息。 |
| `ReviewAgent` | `review` | 擅长检查和改进内容质量，对事物进行评价。 |
| `GreetAgent` | `greet` | 擅长和用户打招呼。 |
| `FileManagerAgent` | `file_manager` | 擅长对文件进行管理。 |

## 任务代理输入

调用任务代理时，路由图会把当前 `RouterState` 和当前路由任务合并为新的输入：

```python
def _build_agent_input(state: RouterState, router: AgentRouter) -> dict[str, Any]:
    return {
        **state,
        "messages": [{"role": "user", "content": router.query}],
    }
```

这意味着：

- 任务代理收到的用户消息是 `router.query`，不是原始完整 `query`
- 原始 `query` 仍保留在状态中
- 当前路由信息保存在 `router` 字段中
- 如果任务代理需要访问请求上下文，应配置 `context_schema`

## 上下文传递

`route` 工具调用内部路由图时会传递当前运行时上下文：

```python
result = await router_agent.ainvoke(
    _build_router_input(runtime.state),
    context=runtime.context,
)
```

内部路由图调用任务代理时，也会从 Pregel runtime 中取出上下文并继续传递：

```python
result = await agent.ainvoke(
    self._build_agent_input(state, router),
    context=self._get_runtime_context(config),
)
```

项目中通常使用 `AppAgentContext` 传递 `user_id`、`chat_id` 等请求级信息。

## 结果提取与合并

任务代理执行完成后，路由图会把输出转换为文本：

```python
{
    "source": source,
    "result": self._extract_result_text(result),
}
```

`_extract_result_text` 支持多种结果形式：

- `str`
- 包含 `messages` 的 `dict`
- 包含 `text` 或 `content` 的 `dict`
- `BaseMessage`
- 包含文本块的 `content_blocks`

`join` 节点根据结果数量决定最终输出：

- 没有结果：返回 `抱歉，没有处理结果`
- 一个结果：直接返回该结果
- 多个结果：使用 `merge_model` 合并为清晰、连贯、无重复的中文回答

## 示例：研究任务代理

`ResearchAgent` 使用 MCP 中间件接入 ArXiv 搜索服务。

```python
class ResearchAgent(RouteTaskAgent):
    def __init__(self):
        agent = create_agent(
            model=create_chat_model(),
            name=SubAgentEnum.RESEARCH.value,
            system_prompt=AGENT_PROMPT_RESEARCH,
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

        super().__init__(
            name=SubAgentEnum.RESEARCH.value,
            description=AGENT_DESCRIPTION_RESEARCH,
            agent=agent,
        )
```

## 示例：文件管理任务代理

`FileManagerAgent` 提供文件读写工具，并对读写操作启用人工审批。

```python
class FileManagerAgent(RouteTaskAgent):
    def __init__(self):
        agent = create_agent(
            model=create_chat_model(enable_thinking=False),
            name=SubAgentEnum.FILE_MANAGER.value,
            system_prompt=AGENT_PROMPT_FILE_MANAGER,
            context_schema=AppAgentContext,
            tools=[read_file, write_file],
            middleware=[
                HumanInTheLoopMiddleware(
                    interrupt_on={
                        "write_file": {...},
                        "read_file": {...},
                    }
                )
            ],
        )

        super().__init__(
            name=SubAgentEnum.FILE_MANAGER.value,
            description=AGENT_DESCRIPTION_FILE_MANAGER,
            agent=agent,
        )
```

## 示例：技能任务代理

`GreetAgent` 使用远程技能加载器加载 greet 技能，并在技能命中时启用 `greet` 工具。

```python
class GreetAgent(RouteTaskAgent):
    def __init__(self):
        agent = create_agent(
            model=create_chat_model(enable_thinking=False),
            name=SubAgentEnum.GREET.value,
            system_prompt=AGENT_PROMPT_GREET,
            context_schema=AppAgentContext,
            state_schema=AppAgentState,
            middleware=[
                SkillsMiddleware(
                    loader=RemoteSkillLoader([
                        "https://raw.githubusercontent.com/dxx/agent-template/refs/heads/main/src/skills/greet/SKILL.md"
                    ]),
                    grouped_tools={
                        "greet": [greet],
                    },
                )
            ],
        )

        super().__init__(
            name=SubAgentEnum.GREET.value,
            description=AGENT_DESCRIPTION_GREET,
            agent=agent,
        )
```

## 新增路由任务代理

新增路由任务代理通常需要 3 步。

### 1. 创建任务代理类

在 `src/agent/router/` 下新增文件，例如 `translate.py`：

```python
from langchain.agents import create_agent

from agent.llm import create_chat_model
from agent.memory.context import AppAgentContext
from agent.middleware import RouteTaskAgent


class TranslateAgent(RouteTaskAgent):
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

### 2. 注册到路由 Agent

在 `src/agent/router/agent.py` 中导入并加入 `agents` 列表：

```python
from agent.router.translate import TranslateAgent

agents = [
    WritingAgent(),
    ResearchAgent(),
    ReviewAgent(),
    GreetAgent(),
    FileManagerAgent(),
    TranslateAgent(),
]
```

### 3. 调整描述

`description` 会直接影响路由模型选择代理，应该写清楚能力边界。

```python
description="擅长翻译和润色多语言内容"
```

## 与 SubAgentMiddleware 的区别

`RouteAgentMiddleware` 和 `SubAgentMiddleware` 都可以把任务交给专门代理，但职责不同。

| 对比项 | `RouteAgentMiddleware` | `SubAgentMiddleware` |
| --- | --- | --- |
| 主 Agent 工具 | `route` | `task` |
| 代理选择方式 | 内部路由模型自动选择 | 主 Agent 指定 `agent_name` |
| 任务拆分位置 | 内部路由图拆分 | 主 Agent 自己拆分 |
| 多代理合并 | 内部 `join` 节点合并 | 主 Agent 读取多个工具结果后自行总结 |
| 适合场景 | 希望统一路由、自动拆分和合并 | 希望主 Agent 精确控制委派目标 |

## 设计建议

- 任务代理名称保持简短稳定，避免频繁变更
- 任务代理描述要明确能力边界，因为路由模型依赖描述做选择
- 路由代理适合“选择谁来做”和“多个结果如何合并”都可以自动化的场景
- 如果需要主 Agent 精确控制每个子任务，应优先考虑 `SubAgentMiddleware`
- 如果多个任务代理都可能处理同一请求，描述中应体现差异，降低误路由概率
- `router_model` 建议使用稳定遵循 JSON 输出的模型
- 多代理合并时不要让 `merge_model` 编造未提供的信息

## 注意事项

- `agents` 不能为空，否则路由没有可用目标
- 任务代理名称不能重复
- `route` 工具只从最近用户消息提取输入，不接收显式参数
- 路由模型输出中不存在的代理名称会被过滤
- 如果路由结果为空，最终返回 `抱歉，没有处理结果`
- 多个任务代理的中间过程默认不会直接展示给用户，用户只看到最终合并结果
- 需要访问上下文时，路由图和任务代理都应配置合适的 `context_schema`
