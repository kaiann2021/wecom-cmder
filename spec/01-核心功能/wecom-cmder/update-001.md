---
title: WeCom Commander-更新001-登录鉴权功能
type: update
update_number: 1
category: 01-核心功能
status: 已确认
update_type: 功能增强
created: 2026-01-30
plan: "[[plan]]"
tags:
  - spec
  - update
  - authentication
  - security
---

# 功能更新方案 - 登录鉴权功能

## 文档关联

- 原设计: [[plan|设计方案]]
- 原总结: [[summary|实现总结]]

---

## 1. 更新背景

### 1.1 问题描述

当前 WeCom Commander 的 Web 管理界面没有任何访问控制，任何人都可以直接访问并修改配置、查看消息历史、管理命令等敏感操作。这存在严重的安全隐患：

- **配置泄露风险**：企业微信的 CorpID、AgentID、Secret 等敏感信息可被任意访问
- **数据泄露风险**：消息历史可能包含敏感业务信息
- **恶意操作风险**：未授权用户可以修改配置、发送消息、管理命令
- **合规风险**：不符合企业安全管理要求

### 1.2 影响范围

- **前端**：所有页面（Dashboard、Config、Messages、Commands）
- **后端**：所有 API 接口（除了企业微信回调接口和健康检查接口）
- **数据库**：需要新增用户表存储用户信息

### 1.3 用户需求

用户希望：
1. 访问 Web 管理界面时需要先登录
2. 只有授权用户才能访问和操作系统
3. 后端 API 需要验证请求的合法性
4. 支持基本的用户管理（初期可以只支持单用户或配置文件管理）

---

## 2. 更新目标

### 2.1 主要目标

1. **前端登录功能**
   - 实现登录页面（Login.vue）
   - 实现路由守卫，未登录用户重定向到登录页
   - 实现 Token 存储和管理
   - 实现自动登出（Token 过期）

2. **后端鉴权功能**
   - 实现 JWT Token 生成和验证
   - 实现登录 API 接口
   - 实现 API 鉴权中间件
   - 保护所有需要鉴权的 API 接口

3. **用户管理**
   - 初期支持配置文件方式管理用户（用户名/密码）
   - 后期可扩展为数据库存储

### 2.2 非目标（明确不做的事情）

- ❌ 不实现复杂的用户权限系统（RBAC）
- ❌ 不实现用户注册功能
- ❌ 不实现密码找回功能
- ❌ 不实现多因素认证（MFA）
- ❌ 不实现 OAuth 第三方登录

---

## 3. 更新方案

### 3.1 方案概述

采用 **JWT (JSON Web Token)** 方案实现登录鉴权：

```
┌─────────────┐                    ┌─────────────┐
│   前端      │                    │   后端      │
│  (Vue 3)    │                    │  (FastAPI)  │
└──────┬──────┘                    └──────┬──────┘
       │                                  │
       │  1. POST /api/v1/auth/login     │
       │     {username, password}         │
       ├─────────────────────────────────>│
       │                                  │
       │  2. 验证用户名密码                │
       │                                  │
       │  3. 返回 JWT Token               │
       │<─────────────────────────────────┤
       │     {access_token, token_type}   │
       │                                  │
       │  4. 存储 Token 到 localStorage   │
       │                                  │
       │  5. 后续请求携带 Token            │
       │     Authorization: Bearer <token>│
       ├─────────────────────────────────>│
       │                                  │
       │  6. 验证 Token                   │
       │                                  │
       │  7. 返回数据                     │
       │<─────────────────────────────────┤
       │                                  │
```

### 3.2 详细设计

#### 3.2.1 后端实现

##### 1. 安全模块（backend/app/core/security.py）

**新增文件**：`backend/app/core/security.py`

```python
"""
安全认证模块

根据 update-001: 添加 JWT 认证功能
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# JWT 配置
SECRET_KEY = "your-secret-key-change-this-in-production"  # 应从环境变量读取
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer 认证
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """验证 JWT Token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

##### 2. 用户配置（backend/app/core/config.py）

**修改文件**：`backend/app/core/config.py`（如果不存在则新增）

```python
"""
配置管理

根据 update-001: 添加用户配置
"""

import os
from typing import Dict

# 用户配置（初期使用配置文件，后期可迁移到数据库）
USERS: Dict[str, str] = {
    # 用户名: 密码哈希
    "admin": "$2b$12$..."  # 默认密码: admin123，应在首次启动时修改
}

# 从环境变量读取
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")  # 应修改为强密码

# JWT 配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24小时
```

##### 3. 认证 Schemas（backend/app/schemas/auth.py）

**新增文件**：`backend/app/schemas/auth.py`

```python
"""
认证相关 Pydantic 模型

根据 update-001: 添加认证 Schemas
"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")


class UserInfo(BaseModel):
    """用户信息"""
    username: str = Field(..., description="用户名")
```

##### 4. 认证 API（backend/app/api/endpoints/auth.py）

**新增文件**：`backend/app/api/endpoints/auth.py`

```python
"""
认证接口

根据 update-001: 添加登录接口
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


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    用户登录

    根据 update-001: 实现登录接口
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
        data={"sub": request.username},
        expires_delta=access_token_expires
    )

    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserInfo)
async def get_current_user(payload: dict = Depends(verify_token)):
    """
    获取当前用户信息

    根据 update-001: 实现获取用户信息接口
    """
    return UserInfo(username=payload["sub"])
```

##### 5. 路由注册（backend/app/api/router.py）

**修改文件**：`backend/app/api/router.py`

```python
# 添加认证路由
from app.api.endpoints import auth

# 在 api_router 中注册
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
```

##### 6. 保护现有 API（backend/app/api/endpoints/*.py）

**修改所有需要保护的接口**，添加依赖注入：

```python
from fastapi import Depends
from app.core.security import verify_token

# 示例：保护配置接口
@router.get("/wechat")
async def get_wechat_config(payload: dict = Depends(verify_token)):
    """获取企业微信配置（需要认证）"""
    # 原有逻辑
    pass
```

**不需要保护的接口**：
- `/api/v1/wechat/callback` - 企业微信回调接口
- `/health` - 健康检查接口

##### 7. 依赖更新（backend/requirements.txt）

**添加依赖**：

```txt
python-jose[cryptography]==3.3.0  # JWT 支持
passlib[bcrypt]==1.7.4            # 密码加密
python-multipart==0.0.6           # 表单数据支持
```

#### 3.2.2 前端实现

##### 1. 登录页面（frontend/src/views/Login.vue）

**新增文件**：`frontend/src/views/Login.vue`

```vue
<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <v-card class="elevation-12">
          <v-toolbar color="primary" dark flat>
            <v-toolbar-title>WeCom Commander 登录</v-toolbar-title>
          </v-toolbar>
          <v-card-text>
            <v-form ref="form" v-model="valid" @submit.prevent="handleLogin">
              <v-text-field
                v-model="username"
                label="用户名"
                prepend-icon="mdi-account"
                :rules="[rules.required]"
                required
              />
              <v-text-field
                v-model="password"
                label="密码"
                prepend-icon="mdi-lock"
                type="password"
                :rules="[rules.required]"
                required
              />
            </v-form>
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn
              color="primary"
              :loading="loading"
              :disabled="!valid"
              @click="handleLogin"
            >
              登录
            </v-btn>
          </v-card-actions>
        </v-card>

        <v-alert
          v-if="error"
          type="error"
          class="mt-4"
          dismissible
          @click:close="error = ''"
        >
          {{ error }}
        </v-alert>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '@/api/client'

const router = useRouter()

const username = ref('')
const password = ref('')
const valid = ref(false)
const loading = ref(false)
const error = ref('')

const rules = {
  required: (value: string) => !!value || '此字段为必填项',
}

const handleLogin = async () => {
  if (!valid.value) return

  loading.value = true
  error.value = ''

  try {
    const response = await apiClient.login({
      username: username.value,
      password: password.value,
    })

    // 存储 Token
    localStorage.setItem('access_token', response.access_token)

    // 跳转到首页
    router.push('/')
  } catch (err: any) {
    error.value = err.response?.data?.detail || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>
```

##### 2. API 客户端更新（frontend/src/api/client.ts）

**修改文件**：`frontend/src/api/client.ts`

```typescript
// 添加认证相关接口

/**
 * 登录请求
 */
export interface LoginRequest {
  username: string
  password: string
}

/**
 * Token 响应
 */
export interface TokenResponse {
  access_token: string
  token_type: string
}

/**
 * 用户信息
 */
export interface UserInfo {
  username: string
}

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: '/api/v1',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // 请求拦截器：添加 Token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // 响应拦截器：处理 401 错误
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token 过期或无效，清除 Token 并跳转到登录页
          localStorage.removeItem('access_token')
          window.location.href = '/login'
        }
        console.error('API Error:', error)
        return Promise.reject(error)
      }
    )
  }

  // ========== 认证接口 ==========

  /**
   * 用户登录
   */
  async login(request: LoginRequest): Promise<TokenResponse> {
    const response = await this.client.post('/auth/login', request)
    return response.data
  }

  /**
   * 获取当前用户信息
   */
  async getCurrentUser(): Promise<UserInfo> {
    const response = await this.client.get('/auth/me')
    return response.data
  }

  /**
   * 登出
   */
  logout(): void {
    localStorage.removeItem('access_token')
    window.location.href = '/login'
  }

  // ... 其他接口保持不变
}
```

##### 3. 路由守卫（frontend/src/router/index.ts）

**修改文件**：`frontend/src/router/index.ts`

```typescript
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/config',
    name: 'Config',
    component: () => import('@/views/Config.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/messages',
    name: 'Messages',
    component: () => import('@/views/Messages.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/commands',
    name: 'Commands',
    component: () => import('@/views/Commands.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  const requiresAuth = to.meta.requiresAuth !== false

  if (requiresAuth && !token) {
    // 需要认证但没有 Token，跳转到登录页
    next('/login')
  } else if (to.path === '/login' && token) {
    // 已登录用户访问登录页，跳转到首页
    next('/')
  } else {
    next()
  }
})

export default router
```

##### 4. 导航栏更新（frontend/src/App.vue）

**修改文件**：`frontend/src/App.vue`

```vue
<template>
  <v-app>
    <v-app-bar v-if="isAuthenticated" app color="primary" dark>
      <v-app-bar-title>WeCom Commander</v-app-bar-title>
      <v-spacer />
      <v-btn icon @click="handleLogout">
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </v-app-bar>

    <v-navigation-drawer v-if="isAuthenticated" app>
      <!-- 导航菜单 -->
    </v-navigation-drawer>

    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '@/api/client'

const router = useRouter()

const isAuthenticated = computed(() => {
  return !!localStorage.getItem('access_token')
})

const handleLogout = () => {
  apiClient.logout()
}
</script>
```

### 3.3 数据结构变更

无需修改现有数据库表，用户信息初期存储在配置文件中。

后期如需扩展，可新增用户表：

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.4 接口变更

| 接口 | 变更类型 | 说明 |
|------|----------|------|
| `POST /api/v1/auth/login` | 新增 | 用户登录接口 |
| `GET /api/v1/auth/me` | 新增 | 获取当前用户信息 |
| 所有其他 API（除回调和健康检查） | 修改 | 添加 Token 验证 |

---

## 4. 实现步骤

### 4.1 步骤清单

**后端实现**：
- [ ] 步骤 1：安装依赖（python-jose、passlib）
- [ ] 步骤 2：创建 `backend/app/core/security.py`
- [ ] 步骤 3：创建 `backend/app/core/config.py`（或修改现有文件）
- [ ] 步骤 4：创建 `backend/app/schemas/auth.py`
- [ ] 步骤 5：创建 `backend/app/api/endpoints/auth.py`
- [ ] 步骤 6：修改 `backend/app/api/router.py` 注册认证路由
- [ ] 步骤 7：修改所有需要保护的 API 接口，添加 `Depends(verify_token)`
- [ ] 步骤 8：生成默认管理员密码哈希

**前端实现**：
- [ ] 步骤 9：创建 `frontend/src/views/Login.vue`
- [ ] 步骤 10：修改 `frontend/src/api/client.ts` 添加认证接口和拦截器
- [ ] 步骤 11：修改 `frontend/src/router/index.ts` 添加路由守卫
- [ ] 步骤 12：修改 `frontend/src/App.vue` 添加登出按钮
- [ ] 步骤 13：更新类型定义 `frontend/src/types/api.ts`

**测试验证**：
- [ ] 步骤 14：测试登录功能
- [ ] 步骤 15：测试 Token 验证
- [ ] 步骤 16：测试路由守卫
- [ ] 步骤 17：测试 Token 过期自动登出
- [ ] 步骤 18：测试企业微信回调接口不受影响

### 4.2 测试计划

**单元测试**：
- [ ] 测试密码加密和验证
- [ ] 测试 JWT Token 生成和验证
- [ ] 测试登录接口（正确/错误密码）
- [ ] 测试 Token 过期处理

**集成测试**：
- [ ] 测试完整登录流程
- [ ] 测试 API 鉴权（有/无 Token）
- [ ] 测试前端路由守卫
- [ ] 测试自动登出

**回归测试**：
- [ ] 确保企业微信回调接口正常工作（不受鉴权影响）
- [ ] 确保健康检查接口正常工作
- [ ] 确保原有功能（配置、消息、命令）正常工作

---

## 5. 风险评估

### 5.1 潜在风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Token 泄露 | 未授权访问 | 1. 使用 HTTPS<br>2. 设置合理的过期时间<br>3. 不在 URL 中传递 Token |
| 密码弱口令 | 账户被破解 | 1. 强制使用强密码<br>2. 文档中提醒修改默认密码 |
| 企业微信回调失败 | 消息接收中断 | 1. 回调接口不添加鉴权<br>2. 充分测试回调功能 |
| Token 过期用户体验差 | 用户频繁登录 | 1. 设置合理的过期时间（24小时）<br>2. 后期可实现 Refresh Token |

### 5.2 回滚方案

如需回滚，执行以下步骤：

1. **后端回滚**：
   - 移除 `backend/app/core/security.py`
   - 移除 `backend/app/schemas/auth.py`
   - 移除 `backend/app/api/endpoints/auth.py`
   - 移除所有 API 接口的 `Depends(verify_token)`
   - 移除新增的依赖包

2. **前端回滚**：
   - 移除 `frontend/src/views/Login.vue`
   - 恢复 `frontend/src/api/client.ts` 的拦截器
   - 恢复 `frontend/src/router/index.ts` 的路由守卫
   - 恢复 `frontend/src/App.vue`

3. **验证**：
   - 确保可以直接访问 Web 界面
   - 确保所有 API 接口正常工作

---

## 6. 验收标准

- [ ] 未登录用户访问任何页面都会跳转到登录页
- [ ] 使用正确的用户名密码可以成功登录
- [ ] 使用错误的用户名密码会显示错误提示
- [ ] 登录后可以正常访问所有页面
- [ ] 所有 API 请求都携带 Token
- [ ] Token 无效或过期时会自动跳转到登录页
- [ ] 点击登出按钮可以成功登出
- [ ] 企业微信回调接口不受鉴权影响，正常工作
- [ ] 健康检查接口不受鉴权影响，正常工作
- [ ] 原有功能（配置、消息、命令）正常工作

---

## 7. 后续优化方向

### 7.1 短期优化（可选）

- [ ] 实现 Refresh Token 机制
- [ ] 实现"记住我"功能
- [ ] 添加登录日志记录
- [ ] 添加密码修改功能

### 7.2 长期扩展（可选）

- [ ] 将用户信息迁移到数据库
- [ ] 实现多用户管理
- [ ] 实现用户权限系统（RBAC）
- [ ] 实现密码找回功能
- [ ] 实现多因素认证（MFA）
- [ ] 集成企业微信 OAuth 登录

---

## 8. 环境变量配置

需要在 `.env` 文件或 Docker Compose 中配置以下环境变量：

```bash
# 管理员账户
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-strong-password-here

# JWT 配置
SECRET_KEY=your-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24小时
```

**重要提醒**：
- 生产环境必须修改默认密码
- SECRET_KEY 必须使用强随机字符串
- 建议使用 HTTPS 部署

---

## 9. 文档更新

需要更新以下文档：

- [ ] `README.md` - 添加登录说明
- [ ] `DEPLOYMENT.md` - 添加环境变量配置说明
- [ ] API 文档 - 添加认证接口文档

---

**更新方案完成日期**: 2026-01-30
**预计实施时间**: 4-6 小时
**风险等级**: 中等
