from typing import Tuple
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool, AsyncConnectionPool
from langgraph.store.postgres import PostgresStore
from langgraph.store.postgres.aio import AsyncPostgresStore
import atexit

from log import get_logger
from config.settings import get_settings

logger = get_logger(__name__)

settiongs = get_settings()

# 配置在配置文件中
# CONNECTION_STRING = "postgresql://postgres:postgres@localhost:5432/langchain"

CONNECTION_STRING = settiongs.postgres_memory_conn_str

def create_async_postgres_store() -> Tuple[AsyncConnectionPool, AsyncPostgresStore]:
    """创建异步的 Postgres store"""
    # 创建连接池
    # 注意：生产环境建议配置好 min_size, max_size 等参数
    conn_pool = AsyncConnectionPool(
        CONNECTION_STRING,
        open=False, # 禁止打开连接，要在异步块中调用 open() 方法
        # 手动管理连接以下参数必须设置
        # see https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint-postgres/README.md
        kwargs={
            "autocommit": True,
            "row_factory": dict_row
        }
    )

    # 在异步块中执行
    # await conn_pool.open()

    # 创建 AsyncPostgresStore
    store = AsyncPostgresStore(conn=conn_pool) # type: ignore[ag-]

    # 在 PostgreSQL 中自动创建相关表
    # 在异步块中执行
    # await store.setup()

    return (conn_pool, store) # type: ignore[arg-type]


def create_postgres_store() -> PostgresStore:
    """创建同步的 Postgres store"""
    # 创建连接池
    # 注意：生产环境建议配置好 min_size, max_size 等参数
    conn_pool = ConnectionPool(
        CONNECTION_STRING,
        open=True,  # 立即打开连接
        kwargs={
            "autocommit": True,
            "row_factory": dict_row
        }
    )

    # 创建 PostgresStore
    store = PostgresStore(conn=conn_pool) # type: ignore[arg-type]

    # 在 PostgreSQL 中自动创建相关表
    store.setup()

    # 定义清理函数
    def cleanup():
        logger.info("正在关闭 Postgre store 连接池...")
          # 关闭池中所有连接
        conn_pool.close()
        logger.info("Postgre store 连接池已关闭...")

    # 注册退出处理器
    # 确保程序正常退出或被信号中断时都能执行清理
    atexit.register(cleanup)

    return store

# 创建全局的 connection pool 和 checkpointer
async_postgres_store_conn_pool, async_postgres_store = create_async_postgres_store()

async def init_postgres_store():
    """初始化 Postgres store"""
    try:
        # 打开 PostgreSQL 连接
        await async_postgres_store_conn_pool.open(wait=True, timeout=10)
        # 在 PostgreSQL 中自动创建相关表
        await async_postgres_store.setup()
        logger.info("Postgre store 初始化完成...")
    except Exception as e:
        logger.error("Postgre store 连接失败", e)
        await close_postgres_store()

async def close_postgres_store():
    """关闭 Postgres store"""
    try:
        logger.info("正在关闭 Postgre store 连接池...")
        # 关闭池中所有连接
        await async_postgres_store_conn_pool.close()
        logger.info("Postgre store 连接池已关闭...")
    except Exception as e:
        logger.error("Postgre store 连接池关闭失败", e)
