"""命令数据模型

根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
章节: 4.3 命令表 (commands)
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class Command(Base):
    """命令表模型"""

    __tablename__ = "commands"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    command_id = Column(String(50), unique=True, nullable=False, comment="命令ID")
    name = Column(String(100), comment="命令名称")
    description = Column(Text, comment="描述")
    category = Column(String(50), comment="分类")
    handler = Column(String(200), comment="处理器路径")
    admin_only = Column(Boolean, default=False, comment="是否仅管理员")
    enabled = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="排序")
    created_at = Column(DateTime, server_default=func.now(), comment="记录创建时间")
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="记录更新时间"
    )

    def __repr__(self):
        return f"<Command(command_id={self.command_id}, name={self.name})>"
