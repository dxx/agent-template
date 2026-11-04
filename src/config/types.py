from enum import StrEnum
from typing import Literal


class AppEnv(StrEnum):
    DEV = "dev"
    PROD = "prod"


ModelProvider = Literal["bailian", "volcengine", "deepseek", "bigmodel", "minimax"]
"""模型提供商。用于按提供商生成个性化请求参数"""
