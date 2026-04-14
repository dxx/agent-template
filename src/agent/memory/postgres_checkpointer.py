from typing import Tuple
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool, AsyncConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
import atexit

from log import get_logger
from config.settings import get_settings

logger = get_logger(__name__)

settiongs = get_settings()

# 配置在配置文件中
# CONNECTION_STRING = "postgresql://postgres:postgres@localhost:5432/langchain"

CONNECTION_STRING = settiongs.postgres_checkpointer_conn_str

def create_async_postgres_checkpointer() -> Tuple[AsyncConnectionPool, AsyncPostgresSaver]:
    """创建异步的 postgres checkpointer"""
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

    # 创建 AsyncPostgresSaver
    checkpointer = AsyncPostgresSaver(conn=conn_pool)

    # 在 PostgreSQL 中自动创建相关表
    # 在异步块中执行
    # await checkpointer.setup()

    return (conn_pool, checkpointer)


def create_postgres_checkpointer() -> PostgresSaver:
    """创建同步的 postgres checkpointer"""
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

    # 创建 PostgresSaver
    checkpointer = PostgresSaver(conn=conn_pool)

    # 在 PostgreSQL 中自动创建相关表
    checkpointer.setup()

    # 定义清理函数
    def cleanup():
        logger.info("正在关闭 Postgres 连接池...")
          # 关闭池中所有连接
        conn_pool.close()
        logger.info("Postgres 连接池已关闭...")

    # 注册退出处理器
    # 确保程序正常退出或被信号中断时都能执行清理
    atexit.register(cleanup)

    return checkpointer
