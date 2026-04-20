# Message 消息模块

消息模块负责管理用户对话的消息记录，包括消息的创建、查询和删除。

## 数据结构

### Message

| 字段             | 类型                      | 说明                      |
| -------------- | ----------------------- | ----------------------- |
| `message_id`   | `str`                   | 消息 ID                   |
| `message_type` | `Literal["user", "agent"]` | 消息类型：user=用户消息，agent=Agent 消息 |
| `content`      | `str`                   | 消息内容                    |

### MessageResponse

| 字段         | 类型              | 说明    |
| ---------- | --------------- | ----- |
| `chat_id`  | `str`           | 对话 ID |
| `messages` | `list[Message]` | 消息列表  |

## API 接口

### 创建新对话

```
POST /message/chat/create
user-token: user_123
```

创建新的对话 ID，每个用户最多创建 10 个对话。

**响应示例：**

```json
{
    "code": 200,
    "message": "success",
    "data": "chat_id_xxx"
}
```

### 获取所有对话消息

```
GET /message/all
user-token: user_123
```

获取当前用户所有对话的消息列表。

**响应示例：**

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "chat_id": "chat_id_xxx",
            "messages": [
                {
                    "message_id": "msg_001",
                    "message_type": "user",
                    "content": "你好"
                },
                {
                    "message_id": "msg_002",
                    "message_type": "agent",
                    "content": "你好，有什么可以帮你的？"
                }
            ]
        }
    ]
}
```

### 获取指定对话消息

```
GET /message/chat/{chat_id}
user-token: user_123
```

**路径参数：**

- `chat_id`: 对话 ID

**响应示例：**

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "message_id": "msg_001",
            "message_type": "user",
            "content": "你好"
        }
    ]
}
```

### 删除指定对话

```
DELETE /message/chat/{chat_id}
user-token: user_123
```

删除指定对话的所有消息，同时从用户的对话列表中移除该 chat_id。

**响应示例：**

```json
{
    "code": 200,
    "message": "success",
    "data": true
}
```

### 删除所有对话

```
DELETE /message/all
user-token: user_123
```

删除用户所有对话的消息和对话记录。

**响应示例：**

```json
{
    "code": 200,
    "message": "success",
    "data": true
}
```

## 存储

- 用户对话 ID 列表存储在 `store` 中，namespace 为 `("user_chat_id",)`，key 为 `user_id`
- 消息内容存储在 `checkpointer` 中，通过 `thread_id = format_thread_id(chat_id, user_id)` 关联

## 限制

- 每个用户最多创建 10 个对话 (`_MAX_CHAT_COUNT = 10`)
