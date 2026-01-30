"""
认证接口

根据 update-001: 添加登录接口和用户信息接口
"""

from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.auth import LoginRequest, TokenResponse, UserInfo
from app.core.security import (
    verify_password,
    create_access_token,
    verify_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.core.config import USERS

router = APIRouter()


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(request: LoginRequest):
    """
    用户登录接口

    根据 update-001: 实现单用户登录功能

    - **username**: 用户名
    - **password**: 密码

    返回 JWT Access Token，有效期 24 小时
    """
    # 验证用户名
    if request.username not in USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    # 验证密码
    hashed_password = USERS[request.username]
    if not verify_password(request.password, hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    # 生成 Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": request.username}, expires_delta=access_token_expires
    )

    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserInfo, summary="获取当前用户信息")
async def get_current_user(payload: dict = Depends(verify_token)):
    """
    获取当前用户信息

    根据 update-001: 实现获取用户信息接口

    需要在请求头中携带有效的 JWT Token：
    ```
    Authorization: Bearer <access_token>
    ```

    返回当前登录用户的信息
    """
    return UserInfo(username=payload["sub"])
