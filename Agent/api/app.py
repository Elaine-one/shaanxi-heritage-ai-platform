# -*- coding: utf-8 -*-
"""
FastAPI应用主文件
提供旅游规划的HTTP API接口
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 添加当前 api 目录到Python路径
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from Agent.agent.agent import get_agent
from Agent.agent.travel_planner import get_travel_planner
from Agent.utils.logger_config import setup_logger
from Agent.api.session_dependencies import close_async_client
from Agent.config.settings import Config
from Agent.api.cache import progress_callbacks
from Agent.api.error_models import error_response

# 导入路由
from Agent.api.edit_endpoints import edit_router
from Agent.api.travel_endpoints import travel_router

# 设置日志
setup_logger()

_cleanup_task = None


async def _progress_cache_cleanup():
    """定期监控进度缓存大小"""
    while True:
        await asyncio.sleep(300)
        logger.debug(f"进度缓存当前大小: {len(progress_callbacks)}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("智能旅游规划Agent API启动")

    from Agent.core.startup import get_startup_manager
    from Agent.core.resource_manager import get_resource_manager

    startup_manager = get_startup_manager()

    init_results = await startup_manager.initialize_all()

    for name, result in init_results.items():
        if not result['success']:
            logger.warning(f"{name} 初始化失败: {result.get('error')}")

    sync_result = await startup_manager.auto_sync_heritage_data()
    if sync_result.get('success'):
        if sync_result.get('skipped'):
            logger.info("数据同步跳过: 数据无变化")
        else:
            logger.info(f"数据同步完成: {sync_result.get('heritage_count', 0)} 条非遗")
    else:
        logger.warning(f"数据同步失败: {sync_result.get('error')}")

    try:
        agent = get_agent()
        planner = get_travel_planner()
        logger.info("核心组件初始化完成")
    except ValueError as e:
        logger.error(f"LLM 模型初始化失败: {str(e)}")
        raise SystemExit(1)
    except Exception as e:
        logger.error(f"核心组件初始化失败: {str(e)}")
        raise SystemExit(1)

    resource_manager = get_resource_manager()
    scheduler_task = asyncio.create_task(resource_manager.start_scheduler())

    global _cleanup_task
    _cleanup_task = asyncio.create_task(_progress_cache_cleanup())

    yield

    logger.info("智能旅游规划Agent API关闭")

    scheduler_task.cancel()
    _cleanup_task.cancel()
    try:
        await asyncio.wait_for(scheduler_task, timeout=5.0)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        pass
    try:
        await asyncio.wait_for(_cleanup_task, timeout=5.0)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        pass

    await close_async_client()

    await resource_manager.shutdown()


# 创建FastAPI应用
app = FastAPI(
    title="非遗旅游规划API",
    description="基于陕西非遗文化的智能旅游规划服务",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
origins_str = Config.AGENT_CORS_ALLOWED_ORIGINS
if not origins_str:
    logger.error("环境变量 AGENT_CORS_ALLOWED_ORIGINS 未配置")
    raise ValueError("Missing required environment variable: AGENT_CORS_ALLOWED_ORIGINS")

origins = [origin.strip() for origin in origins_str.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由器
app.include_router(travel_router)
app.include_router(edit_router)

# ── Unified error response handlers ─────────────────────────────────


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.status_code, exc.detail),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    messages = []
    for err in exc.errors():
        loc = ".".join(str(x) for x in err["loc"])
        messages.append(f"{loc}: {err['msg']}")
    detail = "; ".join(messages)
    return JSONResponse(
        status_code=422,
        content=error_response(422, detail),
    )


@app.exception_handler(Exception)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"未处理异常: {type(exc).__name__}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=error_response(500, "服务器内部错误"),
    )


# ── Basic endpoints ─────────────────────────────────────────────────


@app.get("/")
async def root():
    return {"message": "Agent API Running", "status": "ok"}


@app.get("/health")
async def health_check():
    """健康检查端点"""
    from Agent.memory.session import get_session_pool

    health_info = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }

    try:
        session_pool = get_session_pool()
        redis_health = session_pool.health_check()
        health_info["components"]["session_storage"] = {
            "type": "redis",
            **redis_health
        }
    except Exception as e:
        health_info["components"]["session_storage"] = {
            "type": "unknown",
            "status": "error",
            "error": str(e)
        }

    return health_info


if __name__ == "__main__":
    import uvicorn
    os.makedirs("logs", exist_ok=True)
    os.makedirs("pdf_cache", exist_ok=True)
    uvicorn.run(app, host=os.getenv("AGENT_HOST", "0.0.0.0"), port=int(os.getenv("AGENT_PORT", "8001")))
