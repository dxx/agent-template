import asyncio
import sys
import uvicorn
from typing import Any

from config import get_settings, AppEnv


def selector_loop_factory(use_subprocess: bool = False):
    """Windows 下强制使用 SelectorEventLoop。

    psycopg 的 async 连接池不支持 uvicorn 默认的 ProactorEventLoop。
    必须定义为模块级函数，否则 reload 模式下无法 pickle 传给子进程。
    """
    return asyncio.SelectorEventLoop()


def run():

    # 初始化并获取配置
    settings = get_settings()

    reload = False
    if settings.app_env == AppEnv.DEV.value:
        # 开发环境热更新
        reload = True

    # Windows 下 uvicorn 默认使用 ProactorEventLoop，
    # 但 psycopg 的 async 连接池不支持，必须强制使用 SelectorEventLoop。
    # uvicorn 的 loop 参数类型标注不包含 callable（运行时支持），此处需用 Any 绕过。
    loop: Any
    if sys.platform == "win32":
        loop = selector_loop_factory
    else:
        loop = "auto"

    # 运行 server 模块中的 app 变量
    uvicorn.run(
        app="web.server:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=reload,
        loop=loop,
    )


if __name__ == "__main__":
    run()
