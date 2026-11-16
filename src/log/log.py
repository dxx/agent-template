import logging
import os
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from pythonjsonlogger import json

from config import Settings, get_settings
from config.constants import PROJECT_ROOT
from monitor import get_current_trace_id

settings = get_settings()

# 定义重命名规则：{ "原字段名": "新字段名" }
_rename_fields = {
    "levelname": "log_level",
}

_NA_VALUE = "N/A"

_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class _AppDefaultFilter(logging.Filter):
    """给每条日志记录注入默认字段"""
    def filter(self, record):
        record.app_id = settings.app_id
        record.app_env = settings.app_env
        record.trace_id = get_current_trace_id() or _NA_VALUE
        # log_time format: YYYY-MM-DD HH:mm:ss.SSS
        record.log_time = datetime.fromtimestamp(record.created).strftime(_TIME_FORMAT) + \
            f".{int(record.msecs):03d}"
        record.func_name = record.funcName
        # Remove project path
        relative_pathname = record.pathname.removeprefix(str(PROJECT_ROOT) + os.sep)
        # pathname:no
        record.source = f"{relative_pathname}:{record.lineno}"
        return True


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
            handler.addFilter(_AppDefaultFilter())
            root_logger.addHandler(handler)

    return root_logger

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

def _get_formatter(log_format_type: str) -> logging.Formatter:
    if log_format_type == "json":
        # json 内容
        return json.JsonFormatter(
            fmt="%(levelname)s %(log_time)s %(trace_id)s %(app_env)s %(app_id)s %(name)s" \
                " %(module)s %(func_name)s %(source)s %(message)s",
            json_ensure_ascii=False,
            rename_fields=_rename_fields
        )
    # 文本内容
    return logging.Formatter(
        fmt="[%(levelname)s - %(log_time)s - %(trace_id)s - %(app_env)s - %(app_id)s - %(name)s" \
            " - %(module)s - %(func_name)s - %(source)s] %(message)s"
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
    path = Path(filename)
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)