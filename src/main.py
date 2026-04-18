if __name__ == "__main__":
    import uvicorn

    from config.settings import get_settings

    settings = get_settings()

    reload = False
    if settings.app_env == "default" or "dev":
        # 开发环境热更新
        reload = True

    # 运行 server 模块中的 app 变量
    uvicorn.run(
        app="web.server:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=reload,
    )
