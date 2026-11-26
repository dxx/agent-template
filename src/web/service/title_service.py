"""会话标题生成。

参考 deepseek-harness 的 session-title 设计：只取**用户消息**作为语料，用一个小
模型生成短标题；模型失败或产出为空时，回退为首条消息的截断文本。

标题模型不流式、不思考、限制输出长度，追求快速返回。
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from agent.llm import create_chat_model
from log import get_logger

logger = get_logger(__name__)

# 回退标题的截断长度与最大标题长度
FALLBACK_MAX_CHARS = 12
MAX_TITLE_CHARS = 20
MAX_OUTPUT_TOKENS = 32

_SYSTEM_PROMPT = (
    "你是会话标题生成助手。请根据用户的第一条消息，生成一个简短的中文标题。"
    "要求：不超过 12 个字，概括主题，不要标点、引号、前缀或解释，只输出标题本身。"
)

_title_model = None


def _get_title_model():
    """标题模型实例复用，避免每次请求重复建连。"""
    global _title_model
    if _title_model is None:
        _title_model = create_chat_model(
            enable_thinking=False,
            streaming=False,
            # 限制输出长度，快速返回
            max_tokens=MAX_OUTPUT_TOKENS,
        )
    return _title_model


def _fallback_title(content: str) -> str:
    """确定性回退：取用户消息前若干字符。"""
    text = content.strip().replace("\n", " ")
    text = " ".join(text.split())
    return text[:FALLBACK_MAX_CHARS]


_QUOTES = "\"'“”‘’`「」『』 \t"
_TRAILING_PUNCT = "。．.！!？?；;、，,：:）)】》>"


def _normalize_title(raw: str) -> str:
    """清洗模型输出：取首行、去引号与首尾标点、限制长度。"""
    first = (raw or "").strip().splitlines()[0] if (raw or "").strip() else ""
    text = first.strip(_QUOTES)
    text = text.rstrip(_TRAILING_PUNCT).rstrip()
    text = text.strip(_QUOTES)
    text = " ".join(text.split())
    return text[:MAX_TITLE_CHARS]


async def generate_chat_title(content: str) -> str:
    """根据用户输入内容生成会话标题，失败时回退为截断标题。"""
    fallback = _fallback_title(content)

    try:
        model = _get_title_model()
        response = await model.ainvoke(
            [
                SystemMessage(content=_SYSTEM_PROMPT),
                HumanMessage(content=content),
            ]
        )
        title = _normalize_title(response.text or "")
    except Exception as error:
        logger.warning("生成会话标题失败，回退截断：%s", error)
        return fallback

    return title or fallback
