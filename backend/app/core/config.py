"""
配置管理模块

根据 update-001: 添加用户配置和 JWT 配置
"""

import os
from typing import Dict

# ========== JWT 配置 ==========

# JWT 密钥（生产环境必须修改）
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production-please-use-strong-random-string")

# JWT 算法
ALGORITHM = "HS256"

# Token 过期时间（分钟）
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 默认24小时

# ========== 用户配置（单用户模式） ==========

# 管理员用户名（从环境变量读取）
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")

# 管理员密码（从环境变量读取）
# 注意：这是明文密码，仅用于首次启动时生成哈希
# 生产环境应该使用 ADMIN_PASSWORD_HASH 环境变量直接提供密码哈希
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# 管理员密码哈希（从环境变量读取，优先使用）
# 如果设置了此环境变量，将忽略 ADMIN_PASSWORD
# 生成方式：python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('your_password'))"
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", None)

# 用户存储（单用户模式）
# 格式：{username: password_hash}
# 注意：密码哈希将在应用启动时生成
USERS: Dict[str, str] = {}


def init_users():
    """
    初始化用户配置

    根据 update-001: 单用户模式，从环境变量读取用户信息
    """
    from app.core.security import get_password_hash

    global USERS

    if ADMIN_PASSWORD_HASH:
        # 如果提供了密码哈希，直接使用
        USERS[ADMIN_USERNAME] = ADMIN_PASSWORD_HASH
        print(f"[OK] User '{ADMIN_USERNAME}' loaded (using provided password hash)")
    else:
        # 否则使用明文密码生成哈希
        USERS[ADMIN_USERNAME] = get_password_hash(ADMIN_PASSWORD)
        print(f"[OK] User '{ADMIN_USERNAME}' loaded (password hash generated)")
        print(f"[WARNING] Please change the default password in production!")


# ========== 其他配置 ==========

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/wecom.db")

# 日志级别
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# CORS 配置
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
