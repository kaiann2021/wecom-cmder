"""命令管理接口

根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
章节: 5.4 命令管理接口

更新记录:
- update-001: 添加 API 鉴权
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_token
from app.models.command import Command as DBCommand
from app.schemas.command import (
    CommandListResponse,
    CommandInDB,
    CommandUpdate,
    CommandSyncMenuResponse,
)
from app.services.command import command_manager
from app.services.wechat.client import WeChatClient
from app.api.endpoints.wechat import get_wechat_config

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=CommandListResponse)
async def get_commands(
    db: Session = Depends(get_db),
    _: dict = Depends(verify_token)  # update-001: 添加 Token 验证
):
    """获取命令列表

    根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
    章节: 5.4.1 获取命令列表

    update-001: 需要认证

    Args:
        db: 数据库会话

    Returns:
        CommandListResponse: 命令列表
    """
    try:
        # 从命令管理器获取命令
        commands = command_manager.get_all_commands()

        # 转换为响应模型
        command_list = []
        for cmd in commands:
            command_list.append(
                CommandInDB(
                    id=0,  # 内存中的命令没有数据库ID
                    command_id=cmd.id,
                    name=cmd.name,
                    description=cmd.description,
                    category=cmd.category,
                    handler=cmd.id,  # 使用命令ID作为handler标识
                    admin_only=cmd.admin_only,
                    enabled=cmd.enabled,
                    sort_order=cmd.sort_order,
                )
            )

        return CommandListResponse(commands=command_list)

    except Exception as e:
        logger.error(f"获取命令列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取命令列表失败")


@router.put("/{command_id}")
async def update_command(
    command_id: str,
    update: CommandUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_token)  # update-001: 添加 Token 验证
):
    """更新命令

    根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
    章节: 5.4.2 更新命令

    Args:
        command_id: 命令ID
        update: 更新内容
        db: 数据库会话

    Returns:
        dict: 更新结果
    """
    try:
        # 获取命令
        command = command_manager.get_command(command_id)
        if not command:
            raise HTTPException(status_code=404, detail="命令不存在")

        # 更新命令属性
        if update.enabled is not None:
            command.enabled = update.enabled
        if update.sort_order is not None:
            command.sort_order = update.sort_order

        logger.info(f"更新命令: {command_id}")

        return {"success": True, "message": "命令更新成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新命令失败: {e}")
        raise HTTPException(status_code=500, detail="更新命令失败")


@router.post("/sync-menu", response_model=CommandSyncMenuResponse)
async def sync_menu(
    db: Session = Depends(get_db),
    _: dict = Depends(verify_token)  # update-001: 添加 Token 验证
):
    """同步菜单到企业微信

    根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
    章节: 5.4.3 同步菜单

    update-001: 需要认证

    Args:
        db: 数据库会话

    Returns:
        CommandSyncMenuResponse: 同步结果
    """
    try:
        # 获取配置
        config = get_wechat_config(db)

        # 创建客户端
        client = WeChatClient(
            corp_id=config.corp_id,
            app_secret=config.app_secret,
            agent_id=config.agent_id,
        )

        # 生成菜单数据
        menu_data = command_manager.generate_menu_data()

        # 同步到企业微信
        result = await client.create_menu(menu_data)

        if result.get("success"):
            # 统计菜单数量
            menu_count = sum(
                len(button.get("sub_button", []))
                for button in menu_data.get("button", [])
            )

            return CommandSyncMenuResponse(
                success=True, message="菜单同步成功", menu_count=menu_count
            )
        else:
            return CommandSyncMenuResponse(
                success=False, message="菜单同步失败"
            )

    except Exception as e:
        logger.error(f"同步菜单失败: {e}")
        return CommandSyncMenuResponse(success=False, message=str(e))
