def run():
    import asyncio
    import sys
    import uvicorn

    from config import get_settings, AppEnv
    from log import init_logging

    # 必须在导入其他异步库之前执行
    if sys.platform == "win32":
        # Windows 平台强制使用 SelectorEventLoop
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # 初始化并获取配置
    settings = get_settings()

    # 初始化日志
    init_logging()

    reload = False
    if settings.app_env == AppEnv.DEV.value:
        # 开发环境热更新
        reload = True

    # 运行 server 模块中的 app 变量
    uvicorn.run(
        app="web.server:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=reload,
    )

if __name__ == "__main__":
    run()
