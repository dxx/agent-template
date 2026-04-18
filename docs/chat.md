# Chat 对话模块

对话模块负责处理用户的流式对话请求，支持普通对话和 Human-in-the-Loop 审批流程。

## 数据结构

### 请求类型

#### RequestMsgTypeEnum

| 枚举值        | 说明             |
| ---------- | -------------- |
| `normal`   | 普通消息           |
| `decision` | 决策内容消息（用于审批响应） |

#### ChatRequest

| 字段         | 类型                   | 说明             |
| ---------- | -------------------- | -------------- |
| `msg_type` | `RequestMsgTypeEnum` | 消息类型，默认 normal |
| `content`  | `str`                | 对话请求内容         |
| `decision` | `Decision \| None`   | 审批决策内容         |

### 响应类型

#### ResponseMsgTypeEnum

| 枚举值       | 说明                |
| --------- | ----------------- |
| `normal`  | 普通消息              |
| `process` | 过程处理消息（工具调用、工具结果） |
| `approve` | 审批消息              |
| `error`   | 错误消息              |

#### ChatResponse

| 字段         | 类型                    | 说明        |
| ---------- | --------------------- | --------- |
| `msg_id`   | `str`                 | 消息 ID     |
| `msg_type` | `ResponseMsgTypeEnum` | 消息类型      |
| `content`  | `T \| None`           | 对话响应内容    |
| `approve`  | `Approve \| None`     | 审批内容      |
| `created`  | `int`                 | 创建时间戳（毫秒） |

### 审批相关

#### ApproveItem

| 字段            | 类型                   | 说明      |
| ------------- | -------------------- | ------- |
| `name`        | `str`                | 工具名称    |
| `description` | `str`                | 审批描述    |
| `decisions`   | `list[DecisionType]` | 允许的决策类型 |

#### Approve

| 字段           | 类型                  | 说明    |
| ------------ | ------------------- | ----- |
| `approve_id` | `str`               | 审批 ID |
| `items`      | `list[ApproveItem]` | 审批项列表 |

#### DecisionItem

| 字段              | 类型             | 说明                  |
| --------------- | -------------- | ------------------- |
| `decision_type` | `DecisionType` | 决策类型：approve/reject |
| `description`   | `str`          | 决策描述                |

#### Decision

| 字段            | 类型                   | 说明          |
| ------------- | -------------------- | ----------- |
| `decision_id` | `str`                | 对应中断时的审批 ID |
| `items`       | `list[DecisionItem]` | 决策项列表       |

## API 接口

### 流式对话

```
POST /chat/stream
user-token: user_123
chat-id: chat_4c279fe2-fb7a-40bf-b70c-9cf7604d0a12
```

**请求头：**

- `user-token`: 用户标识
- `chat-id`: 对话 ID。通过 `/message/chat/create` 获得，同一轮对话里面保持相同的 chat-id

**请求体：**

```json
{
    "msg_type": "normal",
    "content": "你好，帮我写一个 hello world 程序"
}
```

**SSE 响应示例：**

```json
// 普通消息
{"msg_id": "xxx", "msg_type": "normal", "content": "你好！", "created": 1234567890}

// 工具调用
{"msg_id": "xxx", "msg_type": "process", "content": "调用: write_file", "created": 1234567890}

// 工具结果
{"msg_id": "xxx", "msg_type": "process", "content": "write_file 执行结果: 写入成功", "created": 1234567890}

// 审批请求
{"msg_id": "xxx", "msg_type": "approve", "approve": {"approve_id": "xxx", "items": [{"name": "write_file", "description": "写入文件需要审批", "decisions": ["approve", "reject"]}]}, "created": 1234567890}

// 错误
{"msg_id": "xxx", "msg_type": "error", "content": "错误信息", "created": 1234567890}
```

## 审批流程

1. **触发中断**：当 Agent 执行需要审批的工具时，触发 Human-in-the-Loop 中断
2. **返回审批信息**：前端收到 `approve` 类型的响应，展示审批内容给用户
3. **提交决策**：用户审批后，前端将决策发送到后端
4. **恢复执行**：后端通过 `decision` 类型的消息恢复 Agent 执行

### 决策请求示例

```json
{
    "msg_type": "decision",
    "content": "",
    "decision": {
        "decision_id": "中断返回的 approve_id",
        "items": [
            {
                "decision_type": "approve",
                "description": "同意写入文件"
            }
        ]
    }
}
```

# 
