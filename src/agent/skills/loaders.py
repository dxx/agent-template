"""技能加载器。"""

import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import override

from agent.skills.helper import parse_skill
from agent.skills.types import Skill
from log import get_logger

logger = get_logger(__name__)

class SkillLoader(ABC):
    """技能加载器。"""

    @abstractmethod
    def list_skills(self) -> list[Skill]:
        """返回可用技能列表。"""

    @abstractmethod
    def get_skill(self, name: str) -> Skill | None:
        """按名称获取技能。"""

    @abstractmethod
    def resolve_source_content(self, file_path: str) -> str:
        """解析并返回资源文件内容。"""

    @abstractmethod
    def reload(self) -> list[Skill]:
        """重新加载技能并返回最新技能列表。"""

    @abstractmethod
    async def areload(self) -> list[Skill]:
        """异步重新加载技能并返回最新技能列表。"""


class DirectorySkillLoader(SkillLoader):
    """从本地目录加载技能。"""

    def __init__(self, dirs: list[str]):
        if not dirs:
            raise ValueError("dirs 不能为空")

        self.skill_dirs = [Path(_resolve_path(directory)).resolve() for directory in dirs]
        self._skills: list[Skill] = []
        self._skills_by_name: dict[str, Skill] = {}
        self.reload()

    @override
    def list_skills(self) -> list[Skill]:
        return list(self._skills)

    @override
    def get_skill(self, name: str) -> Skill | None:
        return self._skills_by_name.get(name)

    @override
    def resolve_source_content(self, file_path: str) -> str:
        path = Path(_resolve_path(file_path)).resolve()
        for skill_dir in self.skill_dirs:
            if path == skill_dir or path.is_relative_to(skill_dir):
                return path.read_text(encoding="utf-8")
        raise ValueError(f"文件路径必须在技能目录中: {file_path}")

    @override
    def reload(self) -> list[Skill]:
        next_skills = self._read_skills()
        next_skills_by_name = self._build_skills_by_name(next_skills)

        self._skills = list(next_skills_by_name.values())
        self._skills_by_name = next_skills_by_name
        return self.list_skills()

    @override
    async def areload(self) -> list[Skill]:
        return self.reload()

    def _build_skills_by_name(self, skills: list[Skill]) -> dict[str, Skill]:
        skills_by_name = {}
        for skill in skills:
            if skill["name"] in skills_by_name:
                logger.warning(
                    "Skill name '%s' is repetitive, keep the old skill. Repetitive skills from '%s'",
                    skill["name"], skill["path"]
                )
                continue
            skills_by_name[skill["name"]] = skill
        return skills_by_name

    def _read_skills(self) -> list[Skill]:
        skills = []
        for skill_directory_path in self.skill_dirs:
            if not skill_directory_path.exists() or not skill_directory_path.is_dir():
                continue

            for path in skill_directory_path.iterdir():
                if not path.is_dir():
                    continue
                skill_path = path.joinpath("SKILL.md")
                if not skill_path.exists():
                    continue
                skill = parse_skill(str(skill_path))
                if not skill:
                    continue

                logger.debug(f"Load skill name: {skill['name']}, path: {skill['path']}")

                skills.append(skill)

        return skills


def _resolve_path(file_path: str) -> str:
    path = ""
    if file_path.startswith("/"):
        path = file_path
    elif re.search(r"^[a-zA-Z]+:", file_path):
        path = file_path
    else:
        work_dir = Path.cwd()
        path = str(work_dir) + "/" + file_path.removeprefix("./")
    return path
