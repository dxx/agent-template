from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore

from agent.memory.postgres_checkpointer import (
    get_async_postgres_checkpointer,
    init_postgres_checkpointer,
    close_postgres_checkpointer,
)
from agent.memory.postgres_store import (
    get_async_postgres_store,
    init_postgres_store,
    close_postgres_store,
)
from config import get_settings


_memory_checkpointer = InMemorySaver()
_memory_store = InMemoryStore()


def get_checkpointer() -> BaseCheckpointSaver:
    if _use_postgres():
        return get_async_postgres_checkpointer()
    return _memory_checkpointer


def get_store() -> BaseStore:
    if _use_postgres():
        return get_async_postgres_store()
    return _memory_store


async def init_checkpointer() -> None:
    if _use_postgres():
        await init_postgres_checkpointer()


async def close_checkpointer() -> None:
    if _use_postgres():
        await close_postgres_checkpointer()


async def init_store() -> None:
    if _use_postgres():
        await init_postgres_store()


async def close_store() -> None:
    if _use_postgres():
        await close_postgres_store()


def _use_postgres() -> bool:
    return get_settings().memory_backend == "postgres"
