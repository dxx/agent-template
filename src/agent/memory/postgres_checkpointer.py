import asyncio
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from log import get_logger
from config import get_settings

logger = get_logger(__name__)

# 全局的 checkpointer 和 connection pool
_async_postgres_checkpointer: AsyncPostgresSaver | None = None
_async_postgres_conn_pool: AsyncConnectionPool | None = None

_init_lock = asyncio.Lock()

# 配置在配置文件中
# CONNECTION_STRING = "postgresql://postgres:postgres@localhost:5432/langchain"


async def init_postgres_checkpointer():
    """初始化 Postgres checkpointer"""
    global _async_postgres_checkpointer, _async_postgres_conn_pool

    if _async_postgres_checkpointer is not None:
        return

    async with _init_lock:
        if _async_postgres_checkpointer is not None:
            return

        settings = get_settings()
        # 注意：生产环境建议配置好 min_size, max_size 等参数
        conn_pool = AsyncConnectionPool(
            settings.postgres_memory_conn_str,
            open=False, # 禁止打开连接，稍后调用 open
            timeout=10,
            # 手动管理连接以下参数必须设置
            # see https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint-postgres/README.md
            kwargs={
                "autocommit": True,
                "row_factory": dict_row
            }
        )

        # 打开连接
        await conn_pool.open(wait=True, timeout=10)

        try:
            # 创建 AsyncPostgresSaver
            checkpointer = AsyncPostgresSaver(conn=conn_pool) # type: ignore[arg-type]

            # 在 PostgreSQL 中自动创建相关表
            await checkpointer.setup()

            _async_postgres_checkpointer = checkpointer
            _async_postgres_conn_pool = conn_pool # type: ignore[arg-type]

            logger.info("Postgre checkpointer 初始化完成...")
        except Exception:
            await conn_pool.close()
            raise

async def close_postgres_checkpointer():
    """关闭 Postgres checkpointer"""
    global _async_postgres_checkpointer, _async_postgres_conn_pool

    async with _init_lock:
        if _async_postgres_conn_pool is None:
            return
        
        try:
            logger.info("正在关闭 Postgres checkpointer 连接池...")
            # 关闭池中所有连接
            await _async_postgres_conn_pool.close()
            logger.info("Postgres checkpointer 连接池已关闭...")
        except Exception as e:
            logger.error("Postgres checkpointer 连接池关闭失败: %s", e)
        finally:
            # 重置全局状态
            _async_postgres_checkpointer = None
            _async_postgres_conn_pool = None


def get_async_postgres_checkpointer() -> AsyncPostgresSaver:
    """获取 Postgres checkpointer"""
    if _async_postgres_checkpointer is None:
        raise RuntimeError("_async_postgres_checkpointer is None. Please initialize first")
    return _async_postgres_checkpointer
