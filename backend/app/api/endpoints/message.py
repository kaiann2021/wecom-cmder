"""消息管理接口

根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
章节: 5.3 消息管理接口
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.database import get_db
from app.models.message import Message
from app.schemas.message import (
    MessageSend,
    MessageSendResponse,
    MessageListQuery,
    MessageListResponse,
    MessageInDB,
)
from app.services.wechat.client import WeChatClient
from app.api.endpoints.wechat import get_wechat_config

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/send", response_model=MessageSendResponse)
async def send_message(
    message: MessageSend, db: Session = Depends(get_db)
):
    """发送消息

    根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
    章节: 5.3.1 发送消息

    Args:
        message: 消息内容
        db: 数据库会话

    Returns:
        MessageSendResponse: 发送结果
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

        # 发送消息
        if message.type == "text":
            if not message.content:
                raise HTTPException(status_code=400, detail="文本消息内容不能为空")

            result = await client.send_text_message(
                content=message.content, to_user=message.to_user
            )

        elif message.type == "news":
            if not message.articles:
                raise HTTPException(status_code=400, detail="图文消息列表不能为空")

            result = await client.send_news_message(
                articles=message.articles, to_user=message.to_user
            )

        else:
            raise HTTPException(status_code=400, detail=f"不支持的消息类型: {message.type}")

        if result.get("success"):
            return MessageSendResponse(success=True, msg_id=result.get("msgid"))
        else:
            return MessageSendResponse(
                success=False, message=result.get("errmsg", "发送失败")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        return MessageSendResponse(success=False, message=str(e))


@router.get("", response_model=MessageListResponse)
async def get_messages(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    direction: str = Query("all", description="消息方向: in/out/all"),
    from_user: str = Query(None, description="发送者筛选"),
    start_time: int = Query(None, description="开始时间（时间戳）"),
    end_time: int = Query(None, description="结束时间（时间戳）"),
    db: Session = Depends(get_db),
):
    """获取消息历史

    根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
    章节: 5.3.2 消息历史

    Args:
        page: 页码
        page_size: 每页数量
        direction: 消息方向
        from_user: 发送者筛选
        start_time: 开始时间
        end_time: 结束时间
        db: 数据库会话

    Returns:
        MessageListResponse: 消息列表
    """
    try:
        # 构建查询
        query = db.query(Message)

        # 方向筛选
        if direction != "all":
            query = query.filter(Message.direction == direction)

        # 发送者筛选
        if from_user:
            query = query.filter(Message.from_user == from_user)

        # 时间范围筛选
        if start_time:
            query = query.filter(Message.create_time >= start_time)
        if end_time:
            query = query.filter(Message.create_time <= end_time)

        # 总数
        total = query.count()

        # 分页
        offset = (page - 1) * page_size
        messages = (
            query.order_by(Message.create_time.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        # 转换为响应模型
        items = [MessageInDB.from_orm(msg) for msg in messages]

        return MessageListResponse(
            total=total, page=page, page_size=page_size, items=items
        )

    except Exception as e:
        logger.error(f"获取消息列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取消息列表失败")
