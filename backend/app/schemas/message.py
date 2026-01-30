"""消息 Pydantic 模型

根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
章节: 5.3 消息管理接口
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    """消息类型枚举"""

    TEXT = "text"
    IMAGE = "image"
    EVENT = "event"
    CLICK = "click"


class MessageDirection(str, Enum):
    """消息方向枚举"""

    IN = "in"
    OUT = "out"


class MessageStatus(str, Enum):
    """消息状态枚举"""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class MessageBase(BaseModel):
    """消息基础模型"""

    msg_type: Optional[str] = None
    from_user: Optional[str] = None
    to_user: Optional[str] = None
    content: Optional[str] = None
    direction: Optional[str] = None


class MessageCreate(MessageBase):
    """创建消息模型"""

    msg_id: str
    create_time: int
    status: str = "pending"


class MessageUpdate(BaseModel):
    """更新消息模型"""

    status: Optional[str] = None
    content: Optional[str] = None


class MessageInDB(MessageBase):
    """数据库消息模型"""

    id: int
    msg_id: str
    create_time: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageSend(BaseModel):
    """发送消息请求模型"""

    type: str = Field(description="消息类型: text|news")
    to_user: str = Field(default="@all", description="接收者UserID")
    content: Optional[str] = Field(None, description="文本消息内容")
    articles: Optional[List[dict]] = Field(None, description="图文消息列表")


class MessageSendResponse(BaseModel):
    """发送消息响应模型"""

    success: bool
    msg_id: Optional[str] = None
    message: Optional[str] = None


class MessageListQuery(BaseModel):
    """消息列表查询参数"""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    direction: Optional[str] = Field(default="all")
    from_user: Optional[str] = None
    start_time: Optional[int] = None
    end_time: Optional[int] = None


class MessageListResponse(BaseModel):
    """消息列表响应模型"""

    total: int
    page: int
    page_size: int
    items: List[MessageInDB]
