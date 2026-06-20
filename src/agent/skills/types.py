from typing import TypedDict


class Skill(TypedDict):
    """技能信息"""

    name: str
    description: str
    content: str
    path: str
