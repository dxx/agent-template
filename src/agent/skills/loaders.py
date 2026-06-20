"""技能加载器。"""

import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import override
from urllib.parse import urljoin, urlparse

import httpx

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
    async def aresolve_source_content(self, file_path: str) -> str:
        """异步解析并返回资源文件内容。"""

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
    async def aresolve_source_content(self, file_path: str) -> str:
        return self.resolve_source_content(file_path)

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
                content = skill_path.read_text(encoding="utf-8")
                skill = parse_skill(content, str(skill_path))
                if not skill:
                    continue

                logger.debug(f"Load skill name: {skill['name']}, path: {skill['path']}")

                skills.append(skill)

        return skills


class RemoteSkillLoader(SkillLoader):
    """从远程 `SKILLS.md` 地址列表加载技能。"""

    def __init__(self, urls: list[str]):
        if not urls:
            raise ValueError("urls 不能为空")
        for url in urls:
            if not _is_http_url(url):
                raise ValueError("urls 必须是 http 或 https 地址")

        self.urls = urls
        self._source_base_urls = {url: urljoin(url, ".") for url in urls}
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
        source_url = self._resolve_source_url(file_path)
        response = httpx.get(source_url)
        response.raise_for_status()
        return response.text

    @override
    async def aresolve_source_content(self, file_path: str) -> str:
        source_url = self._resolve_source_url(file_path)
        async with httpx.AsyncClient() as client:
            response = await client.get(source_url)
            response.raise_for_status()
            return response.text

    @override
    def reload(self) -> list[Skill]:
        next_skills = []
        for url in self.urls:
            response = httpx.get(url)
            response.raise_for_status()
            skill = parse_skill(response.text, url)
            if skill:
                logger.debug(f"Load remote skill name: {skill['name']}, url: {url}")
                next_skills.append(skill)

        self._set_skills(next_skills)
        return self.list_skills()

    @override
    async def areload(self) -> list[Skill]:
        async with httpx.AsyncClient() as client:
            next_skills = []
            for url in self.urls:
                response = await client.get(url)
                response.raise_for_status()
                skill = parse_skill(response.text, url)
                if skill:
                    logger.debug(f"Load remote skill name: {skill['name']}, url: {url}")
                    next_skills.append(skill)

        self._set_skills(next_skills)
        return self.list_skills()

    def _set_skills(self, skills: list[Skill]) -> None:
        skills_by_name = self._build_skills_by_name(skills)
        self._skills = list(skills_by_name.values())
        self._skills_by_name = skills_by_name

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

    def _resolve_source_url(self, file_path: str) -> str:
        if _is_http_url(file_path):
            source_url = file_path
            for source_base_url in self._source_base_urls.values():
                if source_url == source_base_url or source_url.startswith(source_base_url):
                    return source_url
        else:
            for source_base_url in self._source_base_urls.values():
                source_url = urljoin(source_base_url, file_path)
                if source_url == source_base_url or source_url.startswith(source_base_url):
                    return source_url
        raise ValueError(f"资源地址必须在技能来源目录中: {file_path}")


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


def _is_http_url(url: str) -> bool:
    parsed_url = urlparse(url)
    return parsed_url.scheme in {"http", "https"} and parsed_url.netloc != ""
