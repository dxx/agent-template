# MCP (Model Context Protocol) 文档

MCP Client 中间件允许 Agent 连接 MCP Server，动态注入 MCP 服务提供的工具。

## MCPClientMiddleware

### 初始化参数

| 参数                  | 类型                                  | 说明                             |
| ------------------- | ----------------------------------- | ------------------------------ |
| `mcp_config`        | `dict[str, Connection]`             | MCP Server 配置字典                |
| `callbacks`         | `Callbacks \| None`                 | 处理通知和事件的回调函数                   |
| `tool_interceptors` | `list[ToolCallInterceptor] \| None` | 工具调用拦截器列表                      |
| `ignore_tools`      | `list[str] \| None`                 | 忽略的工具名称，以 server name 加 `_` 开头 |

### Connection 配置

MCP Server 连接配置，支持多种传输方式：

```python
mcp_config={
    "server_name": {
        "transport": "stdio",  # 传输类型
        "command": "uvx",      # 启动命令
        "args": ["server_package", "--arg1", "value1"]  # 命令参数
    }
}
```

#### STDIO 传输

```python
{
    "transport": "stdio",
    "command": "uvx",
    "args": ["arxiv-mcp-server", "--storage-path", "./arxiv/paper"]
}
```

#### HTTP/SSE 传输

```python
{
    "transport": "http",
    "url": "http://localhost:8080/sse",
    "headers": {"Authorization": "Bearer token"}
}
```

## 示例

### ReseachAgent

```python
class ReseachAgent(SubAgent):
    def __init__(self):
        super().__init__()
        self._agent = create_agent(
            model=create_chat_model(),
            name=SubAgentEnum.RESEARCH.value,
            system_prompt=AGENT_RESEARCH_PROMPT,
            context_schema=AppAgentContext,
            middleware=[
                # 安装 MCP 中间件
                MCPClientMiddleware(
                    mcp_config={
                        # ArXiv AI搜索服务
                        "arxiv": {
                            "transport": "stdio",
                            "command": "uvx",
                            "args": [
                                "arxiv-mcp-server",
                                "--storage-path",
                                f"{Path.cwd()}/arxiv/paper"
                            ]
                        }
                    }
                )
            ]
        )

    def get_name(self) -> str:
        return SubAgentEnum.RESEARCH.value

    def get_description(self) -> str:
        return "擅长从多个信息源收集和整理信息"
```

### 接口访问

请求：

```bash
### 访问 MCP 工具
POST http://localhost:8000/chat/stream
Content-Type: application/json
Connection: keep-alive
user-token: user_123
chat-id: chat_782e77c0-ddb6-45a7-b8ae-5c16a3f51916

{
  "content": "搜索下关于 Deepseek V3 的论文，总结 50 字给我"
}
```

返回：

```json
data: {"msg_id":"lc_run--019d9f59-5e02-77a1-b0db-9238ff9a3c59","msg_type":"process","content":"调用: task","approve":null,"created":1776494928320}

data: {"msg_id":"lc_run--019d9f59-746f-7e73-9803-c544aef04ad3","msg_type":"process","content":"调用: arxiv_search_papers","approve":null,"created":1776494934487}

data: {"msg_id":"701ae4f1-3592-4299-a520-cf21b5d03832","msg_type":"process","content":"arxiv_search_papers 执行结果: [{'type': 'text', 'text': '{\\n  \"total_results\": 10,\\n  \"papers\": [...], \"categories\": [\\n        \"cs.CL\"\\n         }\\n  ]\\n}', 'id': 'lc_236fd675-baca-4f07-aac6-f70cf5d59db8'}]","approve":null,"created":1776494936586}

data: {"msg_id":"f16a11c2-160b-4292-9d56-02c3929180c2","msg_type":"process","content":"task 执行结果: DeepSeek-V3是671B参数的MoE大模型，采用MLA和DeepSeekMoE架构，无辅助损失负载均衡，训练高效稳定，性能超多数开源模型，可媲美闭源顶尖模型。","approve":null,"created":1776494938470}

data: {"msg_id":"lc_run--019d9f59-8969-7091-86c1-f5ecd0a506ba","msg_type":"normal","content":"Deep","approve":null,"created":1776494939172}

data: {"msg_id":"lc_run--019d9f59-8969-7091-86c1-f5ecd0a506ba","msg_type":"normal","content":"Seek","approve":null,"created":1776494939264}

...
```

## 工作流程

1. **初始化连接**：中间件初始化时连接所有配置的 MCP Server
2. **获取工具**：从 MCP Server 获取可用的工具列表
3. **动态注入**：在模型调用时自动将 MCP 工具添加到工具列表
4. **工具调用**：Agent 调用 MCP 工具时，通过拦截器路由到对应的 MCP Server

## 工具名称前缀

默认启用 `tool_name_prefix=True`，MCP 工具名称会带有前缀，格式为 `{server_name}_{tool_name}`，例如 `arxiv_search`。

这样可以避免不同 MCP Server 提供同名工具时的冲突。

## 忽略特定工具

```python
MCPClientMiddleware(
    mcp_config={...},
    ignore_tools=["weather_search", "news_fetch"]  # 忽略的工具名
)
```

## 工具调用拦截器

可以通过 `tool_interceptors` 参数添加拦截器来修改 MCP 工具的请求与响应：

```python
from langchain_mcp_adapters.interceptors import ToolCallInterceptor

def my_interceptor(tool_call, tool):
    # 修改工具调用
    return tool_call

MCPClientMiddleware(
    mcp_config={...},
    tool_interceptors=[my_interceptor]
)
```
