from agent.memory.context import AppAgentContext
from agent.memory.state import AppAgentState
from agent.memory.postgres_checkpointer import create_async_postgres_checkpointer
from log import get_logger

logger = get_logger(__name__)

# 创建全局的 connection pool 和 checkpointer
async_postgres_conn_pool, async_postgres_checkpointer = create_async_postgres_checkpointer()

async def init_postgres_checkpointer():
    """初始化 Postgres Checkpointer"""
    try:
        # 打开 PostgreSQL 连接
        await async_postgres_conn_pool.open(wait=True, timeout=10)
        # 在 PostgreSQL 中自动创建相关表
        await async_postgres_checkpointer.setup()
    except Exception as e:
        logger.error("PostgreSQL 连接失败", e)
        await close_postgres_checkpointer()

async def close_postgres_checkpointer():
    """关闭 Postgres Checkpointer"""
    try:
        logger.info("正在关闭 Postgres 连接池...")
        # 关闭池中所有连接
        await async_postgres_conn_pool.close()
        logger.info("Postgres 连接池已关闭...")
    except Exception as e:
        logger.error("PostgreSQL 关闭失败", e)

__all__ = [
    "AppAgentContext",
    "AppAgentState",
    "init_postgres_checkpointer",
    "close_postgres_checkpointer"
]
