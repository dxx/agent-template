from langchain.chat_models import init_chat_model, BaseChatModel
from pydantic import SecretStr
from config.settings import get_settings

settings = get_settings()

from langchain.chat_models import init_chat_model
from pydantic import SecretStr
from config.settings import get_settings
settings = get_settings()

def create_chat_model(
    enable_thinking: bool = True,
    reasoning_effort: str = "minimal",
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
    
    stream_token_usage: 流式返回的最后一个数据包包含 Token 消耗信息
    """
    return init_chat_model(
        model=settings.openai_model,
        model_provider="openai",
        base_url=settings.openai_base_url,
        api_key=SecretStr(settings.openai_api_key) if settings.openai_api_key else None,
        temperature=settings.openai_temperature,
        streaming=True,
        stream_usage=stream_token_usage,
        reasoning_effort=reasoning_effort,
        extra_body={
            # https://www.volcengine.com/docs/82379/1449737?lang=zh
            # 字节模型开启思考模式
            "thinking":{"type":"enabled" if enable_thinking else "disabled"},
            # https://help.aliyun.com/zh/model-studio/deep-thinking
            # 千问模型开启思考模式
            "enable_thinking": enable_thinking,
            # 千问模型思考长度
            "thinking_budget": 50,
            # Minimax 将思考字段从 content 中分离出来
            "reasoning_split": True
        }
    )