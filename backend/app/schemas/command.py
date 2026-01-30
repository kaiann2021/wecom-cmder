"""命令 Pydantic 模型

根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
章节: 3.4.2 命令定义, 5.4 命令管理接口
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Callable


class CommandBase(BaseModel):
    """命令基础模型"""

    command_id: str = Field(description="命令ID")
    name: str = Field(description="命令名称")
    description: str = Field(description="命令描述")
    category: str = Field(description="分类（用于菜单分组）")
    admin_only: bool = Field(default=False, description="是否仅管理员可用")


class CommandCreate(CommandBase):
    """创建命令模型"""

    handler: str = Field(description="处理器路径")
    enabled: bool = Field(default=True, description="是否启用")
    sort_order: int = Field(default=0, description="排序")


class CommandUpdate(BaseModel):
    """更新命令模型"""

    enabled: Optional[bool] = None
    sort_order: Optional[int] = None


class CommandInDB(CommandBase):
    """数据库命令模型"""

    id: int
    handler: str
    enabled: bool
    sort_order: int

    class Config:
        from_attributes = True


class CommandListResponse(BaseModel):
    """命令列表响应模型"""

    commands: List[CommandInDB]


class CommandSyncMenuResponse(BaseModel):
    """同步菜单响应模型"""

    success: bool
    message: str
    menu_count: Optional[int] = None
