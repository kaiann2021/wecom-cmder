"""API路由注册

根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
章节: 2.2 目录结构 - app/api/router.py
"""

from fastapi import APIRouter

from app.api.endpoints import wechat, config, message, command

api_router = APIRouter()

# 企业微信回调接口
api_router.include_router(
    wechat.router,
    prefix="/wechat",
    tags=["wechat"],
)

# 配置管理接口
api_router.include_router(
    config.router,
    prefix="/config",
    tags=["config"],
)

# 消息管理接口
api_router.include_router(
    message.router,
    prefix="/messages",
    tags=["messages"],
)

# 命令管理接口
api_router.include_router(
    command.router,
    prefix="/commands",
    tags=["commands"],
)
