# 多模态对话

多模态对话通过 `/chat/stream` 接口提交，复用 Chat 对话模块的流式响应能力。请求体中的 `content` 需要传内容块数组，支持文本、图片和视频。

测试样例见 `tests/multimodal_api.http`。

## 前置要求

多模态能力依赖当前配置的模型是否支持图片或视频理解。使用前请确认模型提供方支持对应输入类型，例如火山方舟、阿里百炼、MiniMax 等多模态模型。

- 火山方舟文档：https://www.volcengine.com/docs/82379/1362931
- 阿里百炼文档：https://help.aliyun.com/zh/model-studio/vision
- MiniMax文档：https://platform.minimaxi.com/docs/api-reference/text-chat-openai

## 请求接口

```http
POST /chat/stream
Content-Type: application/json
Connection: keep-alive
user-token: user_123
chat-id: chat_b3425f93-104f-4987-98e8-523674f967fd
```

请求头说明：

| 请求头 | 说明 |
| --- | --- |
| `user-token` | 用户标识 |
| `chat-id` | 对话 ID。同一轮对话保持相同的 `chat-id` |

## Content 结构

`content` 类型为 `list[Multimodal]`，每个元素是一个内容块。

| 内容块 | 必填字段 | 说明 |
| --- | --- | --- |
| 文本 | `type: "text"`、`text` | 文本提示词 |
| 图片 | `type: "image_url"`、`image_url.url` | 图片 URL 或 Base64 Data URL |
| 视频 | `type: "video_url"`、`video_url.url` | 视频 URL |

文本块：

```json
{
    "type": "text",
    "text": "描述下这个图片"
}
```

图片块：

```json
{
    "type": "image_url",
    "image_url": {
        "url": "https://example.com/demo.png"
    }
}
```

视频块：

```json
{
    "type": "video_url",
    "video_url": {
        "url": "https://example.com/demo.mp4"
    }
}
```

## 图片理解

通过 `image_url.url` 传入可访问的图片地址，并搭配文本块描述任务。

```json
{
    "content": [
        {
            "type": "image_url",
            "image_url": {
                "url": "https://img0.baidu.com/it/u=2944321954,3468161118&fm=253&app=138&f=JPEG?w=800&h=1400"
            }
        },
        {
            "type": "text",
            "text": "描述下这个图片"
        }
    ]
}
```

## Base64 图片

图片也可以通过 Data URL 形式传入 Base64 编码内容。

```json
{
    "content": [
        {
            "type": "image_url",
            "image_url": {
                "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
            }
        },
        {
            "type": "text",
            "text": "描述下这个图片"
        }
    ]
}
```

Base64 内容通常较长，建议仅在图片无法通过公网 URL 访问时使用。

## 视频理解

通过 `video_url.url` 传入可访问的视频地址，并搭配文本块描述任务。

```json
{
    "content": [
        {
            "type": "video_url",
            "video_url": {
                "url": "https://ark-project.tos-cn-beijing.volces.com/doc_video/ark_vlm_video_input.mp4"
            }
        },
        {
            "type": "text",
            "text": "这段视频的内容是什么?"
        }
    ]
}
```

## 可选参数

图片和视频内容块保持 OpenAI 兼容格式，可以在资源对象或内容块中携带模型支持的扩展参数。

图片示例：

```json
{
    "type": "image_url",
    "image_url": {
        "url": "https://example.com/demo.png",
        "detail": "high"
    }
}
```

视频示例：

```json
{
    "type": "video_url",
    "video_url": {
        "url": "https://example.com/demo.mp4",
        "fps": 2
    }
}
```

不同模型对 `detail`、`fps`、图片大小、视频时长等限制不同，实际可用参数以模型提供方文档为准。
