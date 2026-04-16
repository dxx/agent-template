import logging
from logging.handlers import TimedRotatingFileHandler
import sys
from pathlib import Path
from pythonjsonlogger import jsonlogger

from config import get_settings, Settings

settings = get_settings()

# 定义重命名规则：{ "原字段名": "新字段名" }
_rename_fields = {
    "levelname": "level",
    "asctime": "log_time"
}

def init_logging():
    """初始化 logging"""
    formatter = _get_formatter(settings.log_format_type)

    handlers = _get_handlers(settings)

    log_level = settings.log_level if settings.log_level else "INFO"

    level = getattr(logging, log_level.upper())

    # root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if not root_logger.handlers:
        for handler in handlers:
            handler.setLevel(level)
            handler.setFormatter(formatter)
            root_logger.addHandler(handler)

    return root_logger

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

def _get_formatter(log_format_type: str) -> logging.Formatter:
    if log_format_type == "json":
        # json 内容
        return jsonlogger.JsonFormatter( # type: ignore[import]
            fmt="%(levelname)s %(asctime)s %(name)s %(message)s %(pathname)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            json_ensure_ascii=False,
            rename_fields=_rename_fields
        )
    # 文本内容
    return logging.Formatter(
        fmt="[%(levelname)s - %(asctime)s - %(name)s] - %(message)s - %(pathname)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

def _get_handlers(settings: Settings) -> list[logging.Handler]:
    handlers = []
    for handler in settings.log_handlers:
        if handler == "file":
            # 提前创建目录
            _create_dir(settings.log_file)
            handlers.append(
                TimedRotatingFileHandler(
                    filename=settings.log_file,
                    # 按天切割
                    when="D",
                    # 1 个周期，1 天
                    interval=1,
                    # 保留 7 个文件
                    backupCount=7,
                    encoding="utf-8"
                )
            )
        else :
            handlers.append(
                logging.StreamHandler(sys.stdout)
            )
    return handlers

def _create_dir(filename: str):
    path = Path.cwd().joinpath(filename)
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)