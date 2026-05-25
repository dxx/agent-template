from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.store.memory import InMemoryStore
from langgraph.store.base import BaseStore

from agent.memory.postgres_checkpointer import get_async_postgres_checkpointer
from agent.memory.postgres_store import get_async_postgres_store

_memory_checkpointer = InMemorySaver()
_memory_store = InMemoryStore()

def get_checkpointer() -> BaseCheckpointSaver:
    # 生产环境使用 async_postgres_checkpointer, 先在 web/server.py 中初始化
    # return get_async_postgres_checkpointer(),
    return _memory_checkpointer

def get_store() -> BaseStore:
    # 生产环境使用 async_postgres_store, 先在 web/server.py 中初始化
    # return get_async_postgres_store()
    return _memory_store
