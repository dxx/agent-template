from typing import Any
from langchain.chat_models import init_chat_model, BaseChatModel
from pydantic import SecretStr
from config import get_settings, ModelProvider


def create_chat_model(
    enable_thinking: bool = True,
    reasoning_effort: str | None = None,
    max_tokens: int | None = None,
    streaming: bool = True,
    stream_token_usage: bool = True,
    **extra_params: Any,
) -> BaseChatModel:
    """
    创建 OpenAI 兼容的 ChatModel

    Args:
        enable_thinking: 是否启用思考

        reasoning_effort: 调节思考长度，不同平台的模型支持的可选值和默认值不同，具体说明参考各平台的 API 文档。

        max_tokens: 模型输出的最大长度，包含思维链和模型回答。

        streaming: 是否开启流式输出，langchain_openai 会转成 'stream': True 参数
        stream_token_usage: 流式返回的最后一个数据是否包包含 Token 消耗信息，streaming = True 时生效
            如果为 True，langchain_openai 会转成参数： 'stream_options': {'include_usage': True} 传给大模型接口
            如果为 False，没有 'stream_options': {'include_usage': False}

        extra_params: 透传给模型接口的额外参数，会合并进 extra_body，
            同名键以这里传入的为准（可覆盖提供商默认参数）
    """
    settings = get_settings()

    extra_body = _build_extra_body(
        settings.openai_provider,
        enable_thinking,
        stream_token_usage,
        max_tokens,
    )
    extra_body.update(extra_params)

    return init_chat_model(
        model=settings.openai_model,
        model_provider="openai",
        base_url=settings.openai_base_url,
        api_key=SecretStr(settings.openai_api_key) if settings.openai_api_key else None,
        temperature=settings.openai_temperature,
        max_tokens=max_tokens,
        streaming=streaming,
        stream_usage=stream_token_usage,
        reasoning_effort=reasoning_effort,
        extra_body=extra_body,
    )


def _build_extra_body(
    provider: ModelProvider,
    enable_thinking: bool,
    stream_token_usage: bool,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    """根据不同模型提供商生成其支持的额外参数。

    Args:
        stream_token_usage: stream_token_usage = False 时明确传禁用流式 Token 消耗信息:
            'stream_options': {'include_usage': False}，避免有些模型默认是在响应的最后一个
            数据块包含 Token 消耗信息
    """
    extra_body: dict[str, Any] = {}
    if provider == "volcengine":
        # https://www.volcengine.com/docs/82379/1449737?lang=zh
        # 字节模型开启思考模式
        extra_body["thinking"] = {"type": "enabled" if enable_thinking else "disabled"}
        if not stream_token_usage:
            extra_body["stream_options"] = {"include_usage": False}

        return extra_body

    if provider == "deepseek":
        # https://api-docs.deepseek.com/zh-cn/api/create-chat-completion
        # DeepSeek 开启思考模式
        extra_body["thinking"] = {"type": "enabled" if enable_thinking else "disabled"}
        if max_tokens:
            # 外层 max_tokens 会转换成 max_completion_tokens 字段，而 DeepSeek API 暂不支持
            extra_body["max_tokens"] = max_tokens
        if not stream_token_usage:
            extra_body["stream_options"] = {"include_usage": False}

        return extra_body

    if provider == "bigmodel":
        # https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8
        # BigModel 开启思考模式
        extra_body["thinking"] = {"type": "enabled" if enable_thinking else "disabled"}
        if max_tokens:
            # 外层 max_tokens 会转换成 max_completion_tokens 字段，而 BigModel API 暂不支持
            extra_body["max_tokens"] = max_tokens

        # BigModel 没有 stream_options 参数

        return extra_body

    if provider == "minimax":
        # https://platform.minimaxi.com/docs/api-reference/text-openai-api
        # MiniMax-M3 开启 adaptive thinking，关闭时跳过 thinking 直接回答
        # 对于 M2.x 模型，thinking 仍会保持开启
        extra_body["thinking"] = {"type": "adaptive" if enable_thinking else "disabled"}
        # Minimax 将思考字段从 content 中分离出来
        extra_body["reasoning_split"] = True
        if not stream_token_usage:
            extra_body["stream_options"] = {"include_usage": False}

        return extra_body

    if provider == "bailian":
        # https://help.aliyun.com/zh/model-studio/deep-thinking
        # 千问模型开启思考模式
        extra_body["enable_thinking"] = enable_thinking
        if not stream_token_usage:
            extra_body["stream_options"] = {"include_usage": False}

        return extra_body

    raise ValueError(f"不支持的模型提供商: {provider}")
