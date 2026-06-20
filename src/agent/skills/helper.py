"""技能辅助函数。"""

import yaml

from agent.skills.types import Skill
from log import get_logger

logger = get_logger(__name__)

MAX_SKILL_NAME_LENGTH = 64
MAX_SKILL_DESCRIPTION_LENGTH = 1024


def parse_skill(skill_content: str, path: str) -> Skill | None:
    """解析技能定义内容。

    Args:
        skill_content: 技能定义内容，格式与 `SKILL.md` 一致。
        path: 技能定义来源路径或 URL。

    Returns:
        解析成功时返回技能信息；内容为空、缺少 YAML frontmatter 或字段超出限制时返回 None。
    """

    if not skill_content:
        return None

    start_index = skill_content.find("---")
    if start_index < 0:
        return None
    end_index = skill_content.find("---", 3)
    if end_index < 0:
        return None
    frontmatter_str = skill_content[3:end_index].strip()
    frontmatter = yaml.safe_load(frontmatter_str)
    content = skill_content[end_index + 3:].strip()
    skill_name = frontmatter["name"]
    if len(skill_name) > MAX_SKILL_NAME_LENGTH:
        logger.warning("Skill name '%s' exceeds %s characters", skill_name, MAX_SKILL_NAME_LENGTH)
        return None
    skill_description = frontmatter["description"]
    if len(skill_description) > MAX_SKILL_DESCRIPTION_LENGTH:
        logger.warning("Skill description of name '%s' exceeds %s characters", skill_name, MAX_SKILL_NAME_LENGTH)
        return None
    return {
        "name": skill_name,
        "description": skill_description,
        "content": content,
        "path": path
    }
