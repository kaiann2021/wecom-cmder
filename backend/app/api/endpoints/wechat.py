"""企业微信回调接口

根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
章节: 5.1 企业微信回调接口
"""

import logging
from fastapi import APIRouter, Query, Request, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.wechat.crypto import WeChatCrypto, WeChatCryptoException
from app.services.message import MessageService
from app.services.wechat.client import WeChatClient
from app.schemas.config import WeChatConfig
import json

logger = logging.getLogger(__name__)

router = APIRouter()


def get_wechat_config(db: Session = Depends(get_db)) -> WeChatConfig:
    """获取企业微信配置

    Args:
        db: 数据库会话

    Returns:
        WeChatConfig: 企业微信配置

    Raises:
        HTTPException: 配置不存在或不完整时
    """
    from app.models.config import Config

    # 从数据库读取配置
    configs = {}
    config_keys = [
        "wechat.corp_id",
        "wechat.app_secret",
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

    # 验证必填配置
    if not configs.get("corp_id") or not configs.get("app_secret") or not configs.get("agent_id"):
        raise HTTPException(status_code=500, detail="企业微信配置不完整")

    # 构建配置对象（确保字符串类型）
    return WeChatConfig(
        corp_id=str(configs.get("corp_id", "")),
        app_secret=str(configs.get("app_secret", "")),
        agent_id=str(configs.get("agent_id", "")),
        token=configs.get("token"),
        encoding_aes_key=configs.get("encoding_aes_key"),
        admin_users=configs.get("admin_users", []) if isinstance(configs.get("admin_users"), list) else [],
    )


@router.get("/callback", response_class=PlainTextResponse)
async def wechat_verify(
    msg_signature: str = Query(..., description="消息签名"),
    timestamp: str = Query(..., description="时间戳"),
    nonce: str = Query(..., description="随机数"),
    echostr: str = Query(..., description="加密的随机字符串"),
    db: Session = Depends(get_db),
):
    """企业微信URL验证

    根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
    章节: 5.1.1 URL验证
    
    重要：企业微信要求返回纯文本格式（text/plain），不能是 JSON

    Args:
        msg_signature: 消息签名
        timestamp: 时间戳
        nonce: 随机数
        echostr: 加密的随机字符串
        db: 数据库会话

    Returns:
        PlainTextResponse: 解密后的echostr（纯文本）
    """
    try:
        # 获取配置
        config = get_wechat_config(db)

        # 验证配置
        if not config.token or not config.encoding_aes_key:
            raise HTTPException(status_code=500, detail="未配置Token和EncodingAESKey")

        # 初始化加解密器
        crypto = WeChatCrypto(
            token=config.token,
            encoding_aes_key=config.encoding_aes_key,
            corp_id=config.corp_id,
        )

        # 验证URL
        reply_echostr = crypto.verify_url(msg_signature, timestamp, nonce, echostr)

        logger.info(f"企业微信URL验证成功，返回: {reply_echostr[:20]}...")
        
        # 必须返回 PlainTextResponse，企业微信不接受 JSON 格式
        return PlainTextResponse(content=reply_echostr, status_code=200)

    except WeChatCryptoException as e:
        logger.error(f"URL验证失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"URL验证异常: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")


@router.post("/callback")
async def wechat_message(
    request: Request,
    msg_signature: str = Query(..., description="消息签名"),
    timestamp: str = Query(..., description="时间戳"),
    nonce: str = Query(..., description="随机数"),
    db: Session = Depends(get_db),
):
    """接收企业微信消息

    根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
    章节: 5.1.2 消息接收

    Args:
        request: 请求对象
        msg_signature: 消息签名
        timestamp: 时间戳
        nonce: 随机数
        db: 数据库会话

    Returns:
        str: success 或加密的回复消息
    """
    try:
        # 获取配置
        config = get_wechat_config(db)

        # 读取请求体
        body = await request.body()
        encrypted_msg = body.decode("utf-8")

        logger.debug(f"收到企业微信消息: {encrypted_msg[:100]}...")

        # 初始化客户端和服务
        client = WeChatClient(
            corp_id=config.corp_id,
            app_secret=config.app_secret,
            agent_id=config.agent_id,
        )

        message_service = MessageService(
            wechat_config=config, wechat_client=client, db=db
        )

        # 处理消息
        result = await message_service.handle_incoming_message(
            encrypted_msg=encrypted_msg,
            msg_signature=msg_signature,
            timestamp=timestamp,
            nonce=nonce,
        )

        return result or "success"

    except Exception as e:
        logger.error(f"处理消息异常: {e}")
        return "success"  # 即使出错也返回success，避免企业微信重试
