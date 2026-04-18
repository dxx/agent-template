# Human-In-The-Loop 人工介入

`HumanInTheLoopMiddleware` 用于在 Agent 执行特定工具时触发人工审批流程，确保关键操作经过人工确认。

## 使用方式

```python
from agent.middleware import HumanInTheLoopMiddleware
from agent.hitl import approve

middleware = HumanInTheLoopMiddleware[AgentState[Any], AppAgentContext, Any](
    interrupt_on={
        "tool_name": {
            "allowed_decisions": approve.default_allowed_decisions,
            "description": approve.default_descript_callable
        },
    }
)
```

## 配置项

### `interrupt_on`

类型: `dict[str, InterruptConfig]`

指定哪些工具需要触发人工审批。key 为工具名称，value 为 `InterruptConfig` 配置对象。

### `InterruptConfig`

| 字段                  | 类型                   | 说明                                   |
| ------------------- | -------------------- | ------------------------------------ |
| `allowed_decisions` | `list[DecisionType]` | 允许的决策类型，可选值: `"approve"`, `"reject"` |
| `description`       | `str \| Callable`    | 审批描述，可以是字符串或函数                       |

## 审批描述函数

`approve.py` 中提供了默认的审批描述函数 `default_descript_callable`，它使用 LLM 将工具调用信息转换为用户友好的描述：

```python
def default_descript_callable(
    tool_call: ToolCall,
    state: AgentState[Any],
    runtime: Runtime[ContextT]
) -> str:
    """使用 LLM 生成审批描述"""
    content = f"执行工具: {tool_call["name"]}, 参数内容: {tool_call["args"]}\n"
    ai_message = decision_llm.invoke([
        SystemMessage(content=sys_prompt),
        HumanMessage(content=user_prompt.format(content=content))
    ])
    return ai_message.text
```

## 使用示例

在 Agent 中使用：

```python
agent = create_agent(
    model=create_chat_model(enable_thinking=False),
    name="file_manager",
    system_prompt="""你是一个专业的文件管理助手，擅长管理文件相关操作。
                     你的职责是根据用户的需求对文件进行读取、写入等操作
                     请确保你的操作准确、高效。""",
    context_schema=AppAgentContext,
    checkpointer=checkpointer, # 使用 checkpointer
    tools=[read_file, write_file],
    middleware=[
        HumanInTheLoopMiddleware[AgentState[Any], AppAgentContext, Any](
            interrupt_on={
                "write_file": {
                    # 可选的审批
                    "allowed_decisions": approve.default_allowed_decisions,
                    # 审批描述
                    "description": approve.default_descript_callable
                },
                "read_file": {
                    # 可选的审批
                    "allowed_decisions": approve.default_allowed_decisions,
                    # 审批描述
                    "description": "读取文件需要审批"
                },
            }
        ),
        ToolCallsPatchMiddleware()
    ]
)
```

> 某些 LLM 对话时会检查工具调用结果，没有提交审批会导致工具执行结果丢失，使用 `ToolCallsPatchMiddleware` 会补充上一次工具调用丢失的工具消息。

在 Subagent 中使用：

```python
class FileManagerAgent(SubAgent):
    def __init__(self):
        super().__init__()
        self._agent = create_agent(
            model=create_chat_model(enable_thinking=False),
            name=SubAgentEnum.FILE_MANAGER.value,
            system_prompt=AGENT_FILE_MANAGER_PROMPT,
            context_schema=AppAgentContext,
            tools=[read_file, write_file],
            middleware=[
                HumanInTheLoopMiddleware[AgentState[Any], AppAgentContext, Any](
                    interrupt_on={
                        "write_file": {
                            "allowed_decisions": approve.default_allowed_decisions,
                            "description": approve.default_descript_callable
                        },
                        "read_file": {
                            "allowed_decisions": approve.default_allowed_decisions,
                            "description": "读取文件需要审批"
                        },
                    }
                )
            ]
        )

    def get_name(self) -> str:
        return SubAgentEnum.FILE_MANAGER.value

    def get_description(self) -> str:
        return "擅长对文件进行管理"
```

这里 FileManagerAgent 作为一个 Subagent ，默认继承父 Agent 的 checkpointer，不需要配置 checkpointer。

## 触发人工介入

发起请求，访问 FileManagerAgent：

```bash
POST http://localhost:8000/chat/stream
Content-Type: application/json
Connection: keep-alive
user-token: user_123
chat-id: chat_975c7d4b-65e5-4a7f-83a5-6b378b70d2d7

{
  "content": "将 hello 写入文件 hello.txt"
}
```

返回审批信息：

```
data: {"msg_id":"lc_run--019d9eda-16e8-7392-9b0c-969cf4bd4e08","msg_type":"process","content":"调用: task","approve":null,"created":1776486587220}

data: {"msg_id":"lc_run--019d9eda-1b66-7e11-ac84-8e21e1fc2ed6","msg_type":"process","content":"调用: write_file","approve":null,"created":1776486589126}

data: {"msg_id":"05e1073d-0222-4c5b-87ea-615bbe308abd","msg_type":"approve","content":null,"approve":{"approve_id":"e816616e811eb588f3766b02b5c8d6a0","items":[{"name":"write_file","description":"### 审核内容（中文翻译）\n拟执行操作：调用`write_file`工具写入文件\n- 文件路径：`hello.txt`\n- 写入内容：`hello`","decisions":["approve","reject"]}]},"created":1776486589127}
```

approve 消息内容：

```json
{
  "msg_id": "05e1073d-0222-4c5b-87ea-615bbe308abd",
  "msg_type": "approve",
  "content": null,
  "approve": {
    "approve_id": "e816616e811eb588f3766b02b5c8d6a0",
    "items": [{
      "name": "write_file",
      "description": "### 审核内容（中文翻译）\n拟执行操作：调用`write_file`工具写入文件\n- 文件路径：`hello.txt`\n- 写入内容：`hello`",
      "decisions":["approve","reject"]
    }]
  },
  "created":1776486589127
}
```

触发人工介入后，流程中断，需要人工审批。

## 人工审批

进行审批请求：

```bash
POST /chat/stream
Content-Type: application/json
Connection: keep-alive
user-token: user_123
chat-id: chat_975c7d4b-65e5-4a7f-83a5-6b378b70d2d7

{
  "msg_type": "decision",
  "decision": {
    "decision_id": "e816616e811eb588f3766b02b5c8d6a0",
    "items": [
      {
        "decision_type": "approve",
        "description": "同意"
      }
    ]
  }
}
```

decision_id 对应 approve 消息中的 approve_id。

决策类型

- `approve`: 批准操作
- `reject`: 拒绝操作

```
data: {"msg_id":"b43af8a7-18b8-445f-a6bf-4de34b0ce649","msg_type":"process","content":"write_file 执行结果: 写入文件成功","approve":null,"created":1776487002052}

data: {"msg_id":"f0321e7e-9407-4f5d-99fe-ab10bfa1583f","msg_type":"process","content":"task 执行结果: 已成功将内容 \"hello\" 写入文件 hello.txt。","approve":null,"created":1776487002879}

data: {"msg_id":"lc_run--019d9ee0-7302-7b41-b9ac-4e13dec9e2f9","msg_type":"normal","content":"已经","approve":null,"created":1776487003554}

data: {"msg_id":"lc_run--019d9ee0-7302-7b41-b9ac-4e13dec9e2f9","msg_type":"normal","content":"成功","approve":null,"created":1776487003653}

data: {"msg_id":"lc_run--019d9ee0-7302-7b41-b9ac-4e13dec9e2f9","msg_type":"normal","content":"将","approve":null,"created":1776487003653}

data: {"msg_id":"lc_run--019d9ee0-7302-7b41-b9ac-4e13dec9e2f9","msg_type":"normal","content":" \"","approve":null,"created":1776487003653}

data: {"msg_id":"lc_run--019d9ee0-7302-7b41-b9ac-4e13dec9e2f9","msg_type":"normal","content":"hello","approve":null,"created":1776487003689}

data: {"msg_id":"lc_run--019d9ee0-7302-7b41-b9ac-4e13dec9e2f9","msg_type":"normal","content":"\"","approve":null,"created":1776487003689}

data: {"msg_id":"lc_run--019d9ee0-7302-7b41-b9ac-4e13dec9e2f9","msg_type":"normal","content":" ","approve":null,"created":1776487003689}

data: {"msg_id":"lc_run--019d9ee0-7302-7b41-b9ac-4e13dec9e2f9","msg_type":"normal","content":"写入","approve":null,"created":1776487003690}

data: {"msg_id":"lc_run--019d9ee0-7302-7b41-b9ac-4e13dec9e2f9","msg_type":"normal","content":"文件","approve":null,"created":1776487003710}

data: {"msg_id":"lc_run--019d9ee0-7302-7b41-b9ac-4e13dec9e2f9","msg_type":"normal","content":" `","approve":null,"created":1776487003710}

data: {"msg_id":"lc_run--019d9ee0-7302-7b41-b9ac-4e13dec9e2f9","msg_type":"normal","content":"hello","approve":null,"created":1776487003710}

data: {"msg_id":"lc_run--019d9ee0-7302-7b41-b9ac-4e13dec9e2f9","msg_type":"normal","content":".txt","approve":null,"created":1776487003711}

data: {"msg_id":"lc_run--019d9ee0-7302-7b41-b9ac-4e13dec9e2f9","msg_type":"normal","content":"`","approve":null,"created":1776487003754}

data: {"msg_id":"lc_run--019d9ee0-7302-7b41-b9ac-4e13dec9e2f9","msg_type":"normal","content":"。","approve":null,"created":1776487003754}
```