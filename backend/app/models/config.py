"""配置数据模型

根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
章节: 4.2 配置表 (configs)
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class Config(Base):
    """配置表模型"""

    __tablename__ = "configs"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    key = Column(String(100), unique=True, nullable=False, comment="配置键")
    value = Column(Text, comment="配置值（JSON）")
    description = Column(Text, comment="描述")
    created_at = Column(DateTime, server_default=func.now(), comment="记录创建时间")
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="记录更新时间"
    )

    def __repr__(self):
        return f"<Config(key={self.key}, value={self.value})>"
