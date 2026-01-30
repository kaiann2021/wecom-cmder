"""消息数据模型

根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
章节: 4.1 消息表 (messages)
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.sql import func
from app.core.database import Base


class Message(Base):
    """消息表模型"""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    msg_id = Column(String(64), unique=True, index=True, comment="企业微信消息ID")
    msg_type = Column(String(20), comment="消息类型")
    from_user = Column(String(64), index=True, comment="发送者UserID")
    to_user = Column(String(64), comment="接收者")
    content = Column(Text, comment="消息内容")
    create_time = Column(Integer, index=True, comment="创建时间（时间戳）")
    direction = Column(String(10), comment="in/out（接收/发送）")
    status = Column(String(20), comment="状态（pending/sent/failed）")
    created_at = Column(DateTime, server_default=func.now(), comment="记录创建时间")
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="记录更新时间"
    )

    def __repr__(self):
        return f"<Message(id={self.id}, msg_type={self.msg_type}, from_user={self.from_user})>"
