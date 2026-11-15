"""项目公用常量"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
"""项目根目录（与 .env 文件同级）"""

SRC_ROOT = PROJECT_ROOT / "src"
"""源码根目录"""
