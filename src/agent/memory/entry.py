from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.store.memory import InMemoryStore
from langgraph.store.base import BaseStore

from agent.memory.postgres_checkpointer import async_postgres_checkpointer
from agent.memory.postgres_store import async_postgres_store

def get_checkpointer() -> BaseCheckpointSaver:
    # 生产环境使用 async_postgres_checkpointer, 然后在 web/server.py 中初始化
    # return async_postgres_checkpointer,
    return InMemorySaver()

def get_store() -> BaseStore:
    # 生产环境使用 async_postgres_store, 然后在 web/server.py 中初始化
    # return async_postgres_store
    return InMemoryStore()
