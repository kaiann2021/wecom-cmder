"""配置 Pydantic 模型

根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
章节: 3.1.3 配置参数, 5.2 配置管理接口
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class WeChatConfig(BaseModel):
    """企业微信配置模型"""

    corp_id: str = Field(description="企业ID")
    app_secret: str = Field(description="应用Secret")
    agent_id: str = Field(description="应用AgentId")
    proxy: str = Field(default="https://qyapi.weixin.qq.com", description="API代理地址")
    token: Optional[str] = Field(None, description="回调Token")
    encoding_aes_key: Optional[str] = Field(None, description="回调加密Key")
    admin_users: List[str] = Field(default_factory=list, description="管理员白名单")


class WeChatConfigResponse(BaseModel):
    """企业微信配置响应模型（不包含敏感信息）"""

    corp_id: str
    agent_id: str
    proxy: str
    admin_users: List[str]
    token: Optional[str] = None
    encoding_aes_key: Optional[str] = None


class WeChatConfigTest(BaseModel):
    """企业微信配置测试请求模型"""

    corp_id: str
    app_secret: str
    agent_id: str
    token: Optional[str] = None
    encoding_aes_key: Optional[str] = None


class WeChatConfigTestResponse(BaseModel):
    """企业微信配置测试响应模型"""

    success: bool
    message: str
    details: Optional[dict] = None


class ConfigBase(BaseModel):
    """配置基础模型"""

    key: str
    value: str
    description: Optional[str] = None


class ConfigCreate(ConfigBase):
    """创建配置模型"""

    pass


class ConfigUpdate(BaseModel):
    """更新配置模型"""

    value: str


class ConfigInDB(ConfigBase):
    """数据库配置模型"""

    id: int

    class Config:
        from_attributes = True
