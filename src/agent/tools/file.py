import re
from langchain.tools import tool
from pathlib import Path

@tool(parse_docstring=True)
def read_file(file_path: str) -> str:
    """读取文件内容
    
    Args:
        file_path: 文件路径
    """

    file_path = resolve_path(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        return content

@tool(parse_docstring=True)
def write_file(file_path: str, content: str) -> str:
    """写入文件
    
    Args:
        file_path: 文件路径
        content: 写入文件的内容
    """

    file_path = resolve_path(file_path)

    Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return "写入文件成功"


def resolve_path(file_path: str) -> str:
    path = ""
    if file_path.startswith("/"):
        path = file_path
    elif re.search(r"^[a-zA-Z]+:", file_path):
        path = file_path
    else:
        work_dir = Path.cwd()
        path = str(work_dir) + "/" + file_path.removeprefix("./")
    return path
