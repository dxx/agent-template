from typing import Any, Literal
from langchain.chat_models import init_chat_model, BaseChatModel
from pydantic import SecretStr
from config import get_settings

Provider = Literal["bailian", "volcengine", "deepseek", "bigmodel", "minimax"]
"""提供商。主要针对不同的提供商处理个性化参数"""

ReasoningEffort = Literal["minimal", "low", "medium", "high"]
"""思考程度。OpenAI 兼容参数"""


def create_chat_model(
    enable_thinking: bool = True,
    reasoning_effort: ReasoningEffort = "minimal",
    max_tokens: int | None = None,
    streaming: bool = True,
    stream_token_usage: bool = False,
) -> BaseChatModel:
    """
    创建 OpenAI 兼容的 ChatModel

    enable_thinking: 是否启用思考

    reasoning_effort: Chat API 调节思考长度
    - minimal: 关闭思考，直接回答。
    - low: 轻量思考，侧重快速响应。
    - medium: 均衡模式，兼顾速度与深度。
    - high: 深度分析，处理复杂问题。

    max_tokens: 模型输出的最大令牌token数量限制。调用 api 时会将参数转换成 max_completion_tokens 字段

    streaming: 是否开启流式

    stream_token_usage: 流式返回的最后一个数据包包含 Token 消耗信息
    """
    settings = get_settings()
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
        extra_body=_build_extra_body(
            settings.openai_provider, # type: ignore[arg-type]
            enable_thinking
        ),
    )


def _build_extra_body(
    provider: Provider,
    enable_thinking: bool,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    """根据不同模型提供商生成其支持的额外参数。"""

    if provider == "volcengine":
        return {
            # https://www.volcengine.com/docs/82379/1449737?lang=zh
            # 字节模型开启思考模式
            "thinking": {"type": "enabled" if enable_thinking else "disabled"},
        }

    if provider == "deepseek":
        extra_body = {
            # https://api-docs.deepseek.com/zh-cn/api/create-chat-completion
            # DeepSeek 开启思考模式
            "thinking": {"type": "enabled" if enable_thinking else "disabled"},
        }

        if max_tokens:
            # 外层 max_tokens 会转换成 max_completion_tokens 字段，而 DeepSeek API 暂不支持
            extra_body["max_tokens"] = max_tokens # type: ignore[arg-type]

        return extra_body
    
    if provider == "bigmodel":
        extra_body = {
            # https://docs.bigmodel.cn/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8
            # BigModel 开启思考模式
            "thinking": {"type": "enabled" if enable_thinking else "disabled"},
        }

        if max_tokens:
            # 外层 max_tokens 会转换成 max_completion_tokens 字段，而 DeepSeek API 暂不支持
            extra_body["max_tokens"] = max_tokens # type: ignore[arg-type]

        return extra_body

    if provider == "minimax":
        return {
            # https://platform.minimaxi.com/docs/api-reference/text-openai-api
            # MiniMax-M3 开启 adaptive thinking，关闭时跳过 thinking 直接回答
            # 对于 M2.x 模型，thinking 仍会保持开启
            "thinking": {"type": "adaptive" if enable_thinking else "disabled"},
            # Minimax 将思考字段从 content 中分离出来
            "reasoning_split": True,
        }

    return {
        # https://help.aliyun.com/zh/model-studio/deep-thinking
        # 千问模型开启思考模式
        "enable_thinking": enable_thinking,
    }
