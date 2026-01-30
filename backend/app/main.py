"""FastAPI应用入口

根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
章节: 2.2 目录结构 - app/main.py

更新记录:
- update-001: 添加用户配置初始化
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.core.database import init_db
from app.core.config import init_users
from app.api.router import api_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理

    Args:
        app: FastAPI应用实例
    """
    # 启动时执行
    logger.info("正在初始化数据库...")
    init_db()
    logger.info("数据库初始化完成")

    # update-001: 初始化用户配置
    logger.info("正在初始化用户配置...")
    init_users()
    logger.info("用户配置初始化完成")

    yield

    # 关闭时执行
    logger.info("应用正在关闭...")


# 创建FastAPI应用
app = FastAPI(
    title="WeCom Commander",
    description="企业微信指令管理系统",
    version="1.0.0",
    lifespan=lifespan,
)

# 配置CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """根路径

    Returns:
        dict: 欢迎信息
    """
    return {
        "message": "Welcome to WeCom Commander API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """健康检查

    Returns:
        dict: 健康状态
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
