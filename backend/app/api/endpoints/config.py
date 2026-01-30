"""配置管理接口

根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
章节: 5.2 配置管理接口

更新记录:
- update-001: 添加 API 鉴权
"""

import logging
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_token
from app.models.config import Config
from app.schemas.config import (
    WeChatConfig,
    WeChatConfigResponse,
    WeChatConfigTest,
    WeChatConfigTestResponse,
)
from app.services.wechat.client import WeChatClient, WeChatClientException

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/wechat", response_model=WeChatConfigResponse)
async def get_wechat_config(
    db: Session = Depends(get_db),
    _: dict = Depends(verify_token)  # update-001: 添加 Token 验证
):
    """获取企业微信配置

    根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
    章节: 5.2.1 获取配置

    update-001: 需要认证

    Args:
        db: 数据库会话

    Returns:
        WeChatConfigResponse: 企业微信配置（不包含敏感信息）
    """
    try:
        # 从数据库读取配置
        configs = {}
        config_keys = [
            "wechat.corp_id",
            "wechat.agent_id",
            "wechat.token",
            "wechat.encoding_aes_key",
            "wechat.admin_users",
        ]

        for key in config_keys:
            config = db.query(Config).filter(Config.key == key).first()
            if config:
                try:
                    configs[key.replace("wechat.", "")] = json.loads(config.value)
                except:
                    configs[key.replace("wechat.", "")] = config.value

        return WeChatConfigResponse(
            corp_id=configs.get("corp_id", ""),
            agent_id=configs.get("agent_id", ""),
            proxy="https://qyapi.weixin.qq.com",
            admin_users=configs.get("admin_users", []) if isinstance(configs.get("admin_users"), list) else [],
            token=configs.get("token"),
            encoding_aes_key=configs.get("encoding_aes_key"),
        )

    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(status_code=500, detail="获取配置失败")


@router.put("/wechat", response_model=WeChatConfigResponse)
async def update_wechat_config(
    config: WeChatConfig,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_token)  # update-001: 添加 Token 验证
):
    """更新企业微信配置

    根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
    章节: 5.2.2 更新配置

    update-001: 需要认证

    Args:
        config: 企业微信配置
        db: 数据库会话

    Returns:
        WeChatConfigResponse: 更新后的配置
    """
    try:
        # 更新配置到数据库
        config_map = {
            "wechat.corp_id": config.corp_id,
            "wechat.app_secret": config.app_secret,
            "wechat.agent_id": config.agent_id,
            "wechat.token": config.token or "",
            "wechat.encoding_aes_key": config.encoding_aes_key or "",
            "wechat.admin_users": json.dumps(config.admin_users),
        }

        for key, value in config_map.items():
            db_config = db.query(Config).filter(Config.key == key).first()
            if db_config:
                db_config.value = json.dumps(value) if not isinstance(value, str) else value
            else:
                db_config = Config(key=key, value=json.dumps(value) if not isinstance(value, str) else value)
                db.add(db_config)

        db.commit()

        logger.info("企业微信配置更新成功")

        return WeChatConfigResponse(
            corp_id=config.corp_id,
            agent_id=config.agent_id,
            proxy=config.proxy,
            admin_users=config.admin_users,
            token=config.token,
            encoding_aes_key=config.encoding_aes_key,
        )

    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="更新配置失败")


@router.post("/wechat/test", response_model=WeChatConfigTestResponse)
async def test_wechat_config(
    config: WeChatConfigTest,
    _: dict = Depends(verify_token)  # update-001: 添加 Token 验证
):
    """测试企业微信配置

    根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
    章节: 5.2.3 测试配置

    update-001: 需要认证

    Args:
        config: 企业微信配置

    Returns:
        WeChatConfigTestResponse: 测试结果
    """
    try:
        # 创建客户端
        client = WeChatClient(
            corp_id=config.corp_id,
            app_secret=config.app_secret,
            agent_id=config.agent_id,
        )

        # 测试获取 access_token
        token = await client.get_access_token()

        if token:
            return WeChatConfigTestResponse(
                success=True,
                message="配置测试成功",
                details={"token_valid": True},
            )
        else:
            return WeChatConfigTestResponse(
                success=False, message="获取access_token失败"
            )

    except WeChatClientException as e:
        logger.error(f"配置测试失败: {e}")
        return WeChatConfigTestResponse(success=False, message=str(e))
    except Exception as e:
        logger.error(f"配置测试异常: {e}")
        return WeChatConfigTestResponse(success=False, message="配置测试失败")
