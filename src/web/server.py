from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import PlainTextResponse
from fastapi.exceptions import StarletteHTTPException, RequestValidationError

from web.api.routes import router
from web.middleware import ChatMiddleware, AuthMiddleware
from web.schemas import ApiResult, CODE_ERROR, CODE_HTTP_ERROR, CODE_VALIDATION_ERROR
from exception import SystemException
from log import get_logger
from config.settings import get_settings
from utils import json_util
from agent.memory import (
    init_postgres_checkpointer, close_postgres_checkpointer,
    init_postgres_store, close_postgres_store
)

logger = get_logger(__name__)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """生命周期函数"""
    
    logger.info(
        "Application started...",
    )
    logger.info(
        "app_env=%s", settings.app_env
    )

    # 使用 Postgres checkpointer 时打开
    # await init_postgres_checkpointer()

    # 使用 Postgres store 时打开
    # await init_postgres_store()

    # ====== 上面进入上下文，__aenter__ ======
    yield
    # ====== 下面退出上下文，__aexit__ ======

    logger.info("Application shutdown...")
    
    # 使用 Postgres checkpointer 时打开
    # await close_postgres_checkpointer()

    # 使用 Postgres Store 时打开
    # await close_postgres_store()


app = FastAPI(
    title="agent-template",
    description="专用于 AI Agent 服务的项目模版",
    lifespan=lifespan,
    openapi_url=settings.openapi_url
)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc: StarletteHTTPException):
    error_detail = str(exc.detail)

    logger.error(
        "HTTP errors. detail=%s, path=%s",
        error_detail, request.url.path,
        exc_info=exc,
    )
        
    return PlainTextResponse(
        status_code=exc.status_code,
        media_type="application/json;charset=UTF-8",
        content=json_util.to_json(
            ApiResult(code=CODE_HTTP_ERROR, message=error_detail)),
        )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = "Validation errors:"
    for error in exc.errors():
        errors += f"\nField: {error["loc"]}, Error: {error["msg"]}"

    logger.error(
        "Validation errors. erros=%s, path=%s",
        errors, request.url.path,
        exc_info=exc,
    )

    return PlainTextResponse(
        status_code=status.HTTP_200_OK,
        media_type="application/json;charset=UTF-8",
        content=json_util.to_json(
            ApiResult(code=CODE_VALIDATION_ERROR, message=errors)
        ),
    )

@app.exception_handler(SystemException)
async def web_exception_handler(request: Request, exc: SystemException):
    error_detail = str(exc.detail)
    logger.error(
        "System exception. detail=%s, path=%s",
        error_detail, request.url.path,
        exc_info=exc,
    )
    return PlainTextResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        media_type="application/json;charset=UTF-8",
        content=json_util.to_json(ApiResult(code=CODE_ERROR, message=error_detail)),
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    errors = str(exc)
    logger.error(
        "Unhandled exception. erros=%s, path=%s",
        errors, request.url.path,
        exc_info=exc,
    )
    return PlainTextResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        media_type="application/json;charset=UTF-8",
        content=json_util.to_json(ApiResult(code=CODE_ERROR, message=errors)),
    )


app.add_middleware(AuthMiddleware)

app.add_middleware(ChatMiddleware)

app.include_router(router)
