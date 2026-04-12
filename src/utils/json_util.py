import json
from datetime import datetime, date
from enum import Enum
from typing import Any


def to_json[T](obj: T) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, default=_default)


def from_json(json_str: str) -> Any:
    return json.loads(json_str, object_hook=_object_hook)


def _default[T](obj: T) -> T:
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, datetime):
        return obj.isoformat(sep=" ", timespec="seconds")
    if isinstance(obj, date):
        return obj.isoformat()
    if hasattr(obj, "__dict__") and not isinstance(obj, type):
        return obj.__dict__
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _object_hook(obj: dict) -> dict:
    for key, value in obj.items():
        if isinstance(value, str):
            for fmt in (
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
            ):
                try:
                    obj[key] = datetime.strptime(value, fmt)
                    break
                except ValueError:
                    pass
            else:
                try:
                    obj[key] = date.fromisoformat(value)
                except ValueError:
                    pass
    return obj