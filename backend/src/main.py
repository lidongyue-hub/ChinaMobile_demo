import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings
from src.routers import ai, moi
from src.utils.logger import setup_logging

# 初始化日志系统
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up...")
    yield
    logger.info("Application shutting down...")

tags_metadata = [
    {
        "name": "system",
        "description": "系统级接口，例如健康检查。",
    },
    {
        "name": "conversations",
        "description": "会话与消息接口：创建会话、发送消息、上传文件、查看历史。",
    },
]

app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
    description=(
        "AI 对话后端：支持文件上传与历史会话管理。\n\n"
        "核心流程：\n"
        "1️⃣ 创建会话并发送首条消息（可上传文件）\n"
        "2️⃣ 自动生成会话名称（若未提供）\n"
        "3️⃣ 查看会话列表与历史消息\n"
        "4️⃣ 在会话中继续对话，可附带文件与模型参数\n\n"
        "接口文档：/docs, /redoc"
    ),
    version="0.2.0",
    debug=settings.DEBUG,
    openapi_tags=tags_metadata,
)

# 跨域配置：默认允许本地前端，若包含 * 则不携带 credentials
origins_env = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,*",
).split(",")
wildcard = "*" in origins_env

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_env,
    allow_origin_regex=".*" if wildcard else None,
    allow_credentials=not wildcard,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
async def health_check() -> dict:
    return {"status": "ok"}


app.include_router(ai.router, tags=["ai"])
app.include_router(moi.router, tags=["moi"])


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """统一处理 HTTPException，包装为结构化响应。"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "detail": exc.detail,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """兜底异常处理，避免直接暴露内部错误。"""
    logger.exception("Unhandled server error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "detail": "internal server error",
        },
    )


def main() -> None:
    """命令行入口：使用 uvicorn 启动 FastAPI 应用。"""
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    main()

