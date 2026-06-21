# Message 消息模块

消息模块负责管理用户对话的消息记录，包括消息的创建、查询和删除。

## 数据结构

### Message

| 字段       | 类型                   | 说明                      |
| ---------- | ----------------------- | ---------------------- |
| `message_id` | `str`               | 消息 ID                   |
| `message_type` | `Literal["user", "agent"]` | 消息类型：user=用户消息，agent=Agent 消息 |
| `content`  | `str`                 | 消息内容。如果包含图片会用 <msg-img-url> 标签包裹 URL，视频用 msg-video-url 包裹|
| `created`  | `int`                 | 创建时间戳（毫秒）              |

### MessageResponse

| 字段      | 类型              | 说明    |
| --------- | --------------- | ----- |
| `chat_id` | `str`           | 对话 ID |
| `messages` | `list[Message]` | 消息列表  |

## API 接口

### 创建新对话

```http
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

```http
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
                    "content": "你好",
                    "created": 1747988400000
                },
                {
                    "message_id": "msg_002",
                    "message_type": "agent",
                    "content": "你好，有什么可以帮你的？",
                    "created": 1747988405000
                }
            ]
        }
    ]
}
```

### 获取指定对话消息

```http
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
            "content": "你好",
            "created": 1747988400000
        }
    ]
}
```

**多模态响应示例：**

图片：

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "message_id": "3dc8c71a-dc0d-40db-9fdb-0a449a5b430a",
      "message_type": "user",
      "content": "<msg-img-url>https://img0.baidu.com/it/u=2944321954,3468161118&fm=253&app=138&f.jpeg</msg-img-url>\n描述下这个图片",
      "created": 1782031532325
    },
    {
      "message_id": "f1165f32-cdfd-4755-8db4-14f019979656",
      "message_type": "agent",
      "content": "这是一张非常可爱、充满治愈感的图片，画面内容如下：\n\n🐶 **主角**：一只纯白色的萨摩耶幼犬坐在草地上，毛茸茸的非常蓬松。它有着标志性的\"微笑\"表情——嘴巴张开，粉红色的舌头伸出来，眼睛又黑又亮，看起来活泼又开心。\n\n🌸 **前景**：小萨摩耶周围环绕着一片翠绿的草地，草地上点缀着五颜六色的小野花，有粉色、黄色、白色等，色彩缤纷。\n\n🏔️ **中景**：狗狗身后是一片宁静的湖水，湖水呈蓝绿色，清澈平静。湖的两岸散落着一些小木屋和房屋，像是阿尔卑斯山脚下的村落。\n\n⛰️ **远景**：远处是连绵起伏的绿色山脉，山势雄伟，山顶还覆盖着一些白雪，富有层次感。\n\n☁️ **天空**：蔚蓝的天空中飘着大朵大朵洁白的云朵，光线明亮温暖。\n\n整张图片风格偏向 3D 动画/数字艺术风格，色彩饱和度高，画面非常唯美，营造出一种童话般、岁月静好的氛围，让人看了心情都会变好 🌿✨",
      "created": 1782031542825
    }
  ]
}
```

视频：
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "message_id": "b8ad6c74-2962-4d72-950c-f02efc1ceff4",
      "message_type": "user",
      "content": "<msg-video-url>https://ark-project.tos-cn-beijing.volces.com/doc_video/ark_vlm_video_input.mp4</msg-video-url>\n这段视频的内容是什么?",
      "created": 1782031719712
    },
    {
      "message_id": "1396888f-4a45-40f4-95a5-6957c8d6276e",
      "message_type": "agent",
      "content": "这段视频展示的是伦敦的标志性场景，主要内容包括：\n\n🏛️ **大本钟（Big Ben）**：画面左侧是著名的伊丽莎白塔（大本钟），哥特复兴式建筑风格，钟面清晰可见。\n\n🌉 **威斯敏斯特桥（Westminster Bridge）**：画面中央是一座繁忙的大桥，车流不息，有标志性的**红色双层巴士**在桥上行驶。\n\n🌆 **城市景观**：\n- 远处可以看到泰晤士河沿岸的城市天际线\n- 天空中布满戏剧性的云层\n- 整体光线偏暗，呈现黄昏或傍晚的氛围\n- 街灯已经亮起，营造出独特的英伦都市感\n\n🎬 **整体风格**：画面色调偏冷，具有电影质感和复古氛围，展现了伦敦这座城市的历史感与现代都市生活的融合。\n\n> 注：画面右下角有\"AI生成\"的字样，说明这段视频是由AI生成的虚拟场景，而非真实拍摄的伦敦实景。",
      "created": 1782031725792
    }
  ]
}
```

### 删除指定对话

```http
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

```http
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

消息通过 `MessageRecordMiddleware` 中间件记录，存储在 `BaseStore` 中。

### 存储结构

- **namespace**: 可配置，默认为 `("message_history",)`
- **key**: 格式为 `{user_id}:{chat_id}`，从 `runtime.context` 获取
- **value**: `ChatMessageRecord` 对象

### 中间件工作流程

1. **before_agent**: 记录用户最新的 HumanMessage
2. **after_agent**: 记录模型最新的 AIMessage

### 限制条件

- `runtime.context` 必须包含 `user_id` 和 `chat_id` 属性

## 限制

- 每个用户最多创建 10 个对话 (`_MAX_CHAT_COUNT = 10`)