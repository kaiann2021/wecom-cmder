"""数据库连接配置

根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
章节: 4. 数据库设计
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 数据库URL配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/wecom.db")

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


def get_db():
    """获取数据库会话

    Yields:
        Session: 数据库会话对象
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库

    创建所有表并插入初始数据
    """
    from app.models import message, config, command

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    # 插入初始配置
    db = SessionLocal()
    try:
        from app.models.config import Config

        # 检查是否已有配置
        existing_configs = db.query(Config).count()
        if existing_configs == 0:
            # 插入默认配置
            default_configs = [
                Config(key="wechat.corp_id", value='""', description="企业ID"),
                Config(key="wechat.app_secret", value='""', description="应用Secret"),
                Config(key="wechat.agent_id", value='""', description="应用AgentId"),
                Config(key="wechat.token", value='""', description="回调Token"),
                Config(key="wechat.encoding_aes_key", value='""', description="回调加密Key"),
                Config(key="wechat.admin_users", value='[]', description="管理员白名单"),
            ]
            db.add_all(default_configs)
            db.commit()
    finally:
        db.close()
