# 企业微信指令管理系统 (WeCom Commander) 技术规格文档

## 1. 项目概述

### 1.1 项目背景
基于 MoviePilot 项目精简而来，专注于企业微信集成功能，提供一个轻量级的企业微信指令管理和消息推送系统。

### 1.2 核心功能
1. **消息推送** - 发送文本、图片、卡片等消息到企业微信
2. **指令接收** - 接收企业微信消息并解析为程序指令
3. **菜单交互** - 配置和响应企业微信应用菜单
4. **OAuth认证** - 企业微信用户身份验证和授权（基础实现）

### 1.3 技术栈
- **后端**: Python 3.11 + FastAPI
- **前端**: Vue 3 + TypeScript + Vuetify
- **数据库**: SQLite (可扩展为 PostgreSQL/MySQL)
- **容器化**: Docker + Docker Compose

---

## 2. 系统架构

### 2.1 整体架构
```
┌─────────────────────────────────────────────────────────┐
│                    企业微信服务器                          │
└────────────────────┬────────────────────────────────────┘
                     │ (Webhook/API)
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   WeCom Commander                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  API Layer   │  │  Service     │  │  Database    │  │
│  │  (FastAPI)   │◄─┤  Layer       │◄─┤  (SQLite)    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         ▲                  ▲                            │
│         │                  │                            │
│  ┌──────┴──────────────────┴──────┐                    │
│  │     Frontend (Vue 3)            │                    │
│  └─────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

### 2.2 目录结构
```
wecom-cmder/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── api/               # API路由
│   │   │   ├── endpoints/     # 端点实现
│   │   │   │   ├── message.py # 消息接收/发送
│   │   │   │   ├── config.py  # 配置管理
│   │   │   │   └── command.py # 命令管理
│   │   │   └── router.py      # 路由注册
│   │   ├── core/              # 核心模块
│   │   │   ├── config.py      # 配置管理
│   │   │   ├── security.py    # 安全认证
│   │   │   └── database.py    # 数据库连接
│   │   ├── models/            # 数据模型
│   │   │   ├── message.py     # 消息模型
│   │   │   ├── config.py      # 配置模型
│   │   │   └── command.py     # 命令模型
│   │   ├── schemas/           # Pydantic模型
│   │   │   ├── message.py
│   │   │   ├── config.py
│   │   │   └── command.py
│   │   ├── services/          # 业务逻辑
│   │   │   ├── wechat/        # 企业微信服务
│   │   │   │   ├── client.py  # API客户端
│   │   │   │   ├── crypto.py  # 消息加解密
│   │   │   │   ├── parser.py  # 消息解析
│   │   │   │   └── menu.py    # 菜单管理
│   │   │   ├── message.py     # 消息处理
│   │   │   └── command.py     # 命令处理
│   │   └── main.py            # 应用入口
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # 前端代码
│   ├── src/
│   │   ├── api/               # API调用
│   │   ├── components/        # 组件
│   │   ├── views/             # 页面
│   │   │   ├── Dashboard.vue  # 仪表盘
│   │   │   ├── Config.vue     # 配置页面
│   │   │   ├── Messages.vue   # 消息历史
│   │   │   └── Commands.vue   # 命令管理
│   │   ├── router/            # 路由
│   │   ├── stores/            # 状态管理
│   │   └── main.ts
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 3. 核心模块设计

### 3.1 企业微信客户端 (WeChat Client)

#### 3.1.1 功能职责
- 管理 Access Token 获取和缓存
- 封装企业微信 API 调用
- 处理 API 错误和重试

#### 3.1.2 核心方法
```python
class WeChatClient:
    def __init__(self, corp_id: str, app_secret: str, agent_id: str):
        """初始化客户端"""

    async def get_access_token(self) -> str:
        """获取访问令牌（带缓存）"""

    async def send_text_message(self, content: str, to_user: str = "@all") -> dict:
        """发送文本消息"""

    async def send_news_message(self, articles: List[Article], to_user: str = "@all") -> dict:
        """发送图文消息"""

    async def create_menu(self, menu_data: dict) -> dict:
        """创建应用菜单"""

    async def delete_menu(self) -> dict:
        """删除应用菜单"""
```

#### 3.1.3 配置参数
```python
class WeChatConfig(BaseModel):
    corp_id: str                    # 企业ID
    app_secret: str                 # 应用Secret
    agent_id: str                   # 应用AgentId
    proxy: str = "https://qyapi.weixin.qq.com"  # API代理地址
    token: Optional[str] = None     # 回调Token
    encoding_aes_key: Optional[str] = None  # 回调加密Key
    admin_users: List[str] = []     # 管理员白名单
```

---

### 3.2 消息加解密 (Message Crypto)

#### 3.2.1 功能职责
- 实现企业微信消息加解密协议
- 验证消息签名
- URL验证

#### 3.2.2 核心方法
```python
class WeChatCrypto:
    def __init__(self, token: str, encoding_aes_key: str, corp_id: str):
        """初始化加解密器"""

    def verify_url(self, msg_signature: str, timestamp: str, nonce: str, echo_str: str) -> str:
        """验证URL（企业微信回调验证）"""

    def decrypt_message(self, msg_signature: str, timestamp: str, nonce: str, encrypt_msg: str) -> str:
        """解密消息"""

    def encrypt_message(self, reply_msg: str, nonce: str, timestamp: str) -> tuple:
        """加密消息"""
```

#### 3.2.3 依赖库
- `pycryptodome` - AES加密
- `xmltodict` - XML解析

---

### 3.3 消息解析器 (Message Parser)

#### 3.3.1 功能职责
- 解析企业微信回调消息
- 提取消息类型和内容
- 权限验证

#### 3.3.2 消息类型
```python
class MessageType(Enum):
    TEXT = "text"           # 文本消息
    IMAGE = "image"         # 图片消息
    EVENT = "event"         # 事件消息
    CLICK = "click"         # 菜单点击
```

#### 3.3.3 解析流程
```python
class MessageParser:
    def parse(self, xml_data: str) -> ParsedMessage:
        """
        解析消息流程：
        1. XML转字典
        2. 提取基础字段（MsgType, FromUserName, CreateTime等）
        3. 根据类型提取特定字段
        4. 返回结构化消息对象
        """
```

---

### 3.4 命令管理器 (Command Manager)

#### 3.4.1 功能职责
- 注册和管理系统命令
- 命令路由和执行
- 菜单自动生成

#### 3.4.2 命令定义
```python
class Command(BaseModel):
    id: str                     # 命令ID
    name: str                   # 命令名称
    description: str            # 命令描述
    category: str               # 分类（用于菜单分组）
    handler: Callable           # 处理函数
    admin_only: bool = False    # 是否仅管理员可用
```

#### 3.4.3 内置命令示例
```python
BUILTIN_COMMANDS = [
    Command(
        id="status",
        name="系统状态",
        description="查看系统运行状态",
        category="系统",
        handler=handle_status
    ),
    Command(
        id="help",
        name="帮助",
        description="查看命令列表",
        category="系统",
        handler=handle_help
    ),
    # 可扩展更多命令...
]
```

---

### 3.5 消息处理服务 (Message Service)

#### 3.5.1 功能职责
- 接收和处理企业微信消息
- 消息持久化
- 消息分发

#### 3.5.2 处理流程
```python
class MessageService:
    async def handle_incoming_message(self, encrypted_msg: str, signature: str, timestamp: str, nonce: str):
        """
        处理流程：
        1. 解密消息
        2. 解析消息
        3. 权限验证
        4. 保存消息记录
        5. 根据类型分发处理
           - 文本消息 → 命令解析
           - 事件消息 → 事件处理
        6. 返回响应
        """
```

---

## 4. 数据库设计

### 4.1 消息表 (messages)
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    msg_id VARCHAR(64) UNIQUE,          -- 企业微信消息ID
    msg_type VARCHAR(20),                -- 消息类型
    from_user VARCHAR(64),               -- 发送者UserID
    to_user VARCHAR(64),                 -- 接收者
    content TEXT,                        -- 消息内容
    create_time INTEGER,                 -- 创建时间（时间戳）
    direction VARCHAR(10),               -- in/out（接收/发送）
    status VARCHAR(20),                  -- 状态（pending/sent/failed）
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_msg_from_user ON messages(from_user);
CREATE INDEX idx_msg_create_time ON messages(create_time);
```

### 4.2 配置表 (configs)
```sql
CREATE TABLE configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key VARCHAR(100) UNIQUE NOT NULL,   -- 配置键
    value TEXT,                          -- 配置值（JSON）
    description TEXT,                    -- 描述
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 预置配置项
INSERT INTO configs (key, value, description) VALUES
('wechat.corp_id', '""', '企业ID'),
('wechat.app_secret', '""', '应用Secret'),
('wechat.agent_id', '""', '应用AgentId'),
('wechat.token', '""', '回调Token'),
('wechat.encoding_aes_key', '""', '回调加密Key'),
('wechat.admin_users', '[]', '管理员白名单');
```

### 4.3 命令表 (commands)
```sql
CREATE TABLE commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command_id VARCHAR(50) UNIQUE NOT NULL, -- 命令ID
    name VARCHAR(100),                       -- 命令名称
    description TEXT,                        -- 描述
    category VARCHAR(50),                    -- 分类
    handler VARCHAR(200),                    -- 处理器路径
    admin_only BOOLEAN DEFAULT 0,            -- 是否仅管理员
    enabled BOOLEAN DEFAULT 1,               -- 是否启用
    sort_order INTEGER DEFAULT 0,            -- 排序
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. API接口设计

### 5.1 企业微信回调接口

#### 5.1.1 URL验证
```
GET /api/v1/wechat/callback
Query Parameters:
  - msg_signature: 消息签名
  - timestamp: 时间戳
  - nonce: 随机数
  - echostr: 加密的随机字符串

Response: 解密后的echostr（纯文本）
```

#### 5.1.2 消息接收
```
POST /api/v1/wechat/callback
Query Parameters:
  - msg_signature: 消息签名
  - timestamp: 时间戳
  - nonce: 随机数
Body: XML格式的加密消息

Response: success 或加密的回复消息
```

---

### 5.2 配置管理接口

#### 5.2.1 获取配置
```
GET /api/v1/config/wechat
Response:
{
  "corp_id": "string",
  "agent_id": "string",
  "proxy": "string",
  "admin_users": ["user1", "user2"],
  "token": "string",
  "encoding_aes_key": "string"
}
```

#### 5.2.2 更新配置
```
PUT /api/v1/config/wechat
Body:
{
  "corp_id": "string",
  "app_secret": "string",
  "agent_id": "string",
  "token": "string",
  "encoding_aes_key": "string",
  "admin_users": ["user1"]
}
Response: 更新后的配置
```

#### 5.2.3 测试配置
```
POST /api/v1/config/wechat/test
Body: 同更新配置
Response:
{
  "success": true,
  "message": "配置测试成功",
  "details": {
    "token_valid": true,
    "menu_created": true
  }
}
```

---

### 5.3 消息管理接口

#### 5.3.1 发送消息
```
POST /api/v1/messages/send
Body:
{
  "type": "text|news",
  "to_user": "@all",
  "content": "消息内容",
  "articles": [...]  // 图文消息时使用
}
Response:
{
  "success": true,
  "msg_id": "string"
}
```

#### 5.3.2 消息历史
```
GET /api/v1/messages
Query Parameters:
  - page: 页码（默认1）
  - page_size: 每页数量（默认20）
  - direction: in/out/all（默认all）
  - from_user: 发送者筛选
  - start_time: 开始时间
  - end_time: 结束时间

Response:
{
  "total": 100,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": 1,
      "msg_id": "xxx",
      "msg_type": "text",
      "from_user": "user1",
      "content": "消息内容",
      "create_time": 1234567890,
      "direction": "in"
    }
  ]
}
```

---

### 5.4 命令管理接口

#### 5.4.1 获取命令列表
```
GET /api/v1/commands
Response:
{
  "commands": [
    {
      "id": "status",
      "name": "系统状态",
      "description": "查看系统运行状态",
      "category": "系统",
      "admin_only": false,
      "enabled": true
    }
  ]
}
```

#### 5.4.2 更新命令
```
PUT /api/v1/commands/{command_id}
Body:
{
  "enabled": true,
  "sort_order": 1
}
```

#### 5.4.3 同步菜单
```
POST /api/v1/commands/sync-menu
Response:
{
  "success": true,
  "message": "菜单同步成功",
  "menu_count": 5
}
```

---

## 6. 前端页面设计

### 6.1 仪表盘 (Dashboard)
- 系统运行状态
- 今日消息统计
- 最近消息列表
- 快捷操作按钮

### 6.2 配置页面 (Config)
- 企业微信配置表单
  - 企业ID
  - 应用Secret
  - 应用AgentId
  - 回调Token
  - 回调加密Key
  - 管理员白名单
- 配置测试按钮
- 保存按钮

### 6.3 消息历史 (Messages)
- 消息列表（表格）
  - 时间
  - 方向（收/发）
  - 发送者
  - 消息类型
  - 内容预览
- 筛选器
  - 时间范围
  - 方向
  - 发送者
- 分页

### 6.4 命令管理 (Commands)
- 命令列表（卡片）
  - 命令名称
  - 描述
  - 分类
  - 启用/禁用开关
- 拖拽排序
- 同步菜单按钮

---

## 7. Docker部署

### 7.1 docker-compose.yml
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    container_name: wecom-cmder-backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_URL=sqlite:///data/wecom.db
      - LOG_LEVEL=INFO
    restart: unless-stopped

  frontend:
    build: ./frontend
    container_name: wecom-cmder-frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: wecom-cmder-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
```

### 7.2 环境变量
```env
# 数据库
DATABASE_URL=sqlite:///data/wecom.db

# 日志
LOG_LEVEL=INFO

# CORS（开发环境）
CORS_ORIGINS=http://localhost:3000

# JWT密钥（可选，用于Web认证）
SECRET_KEY=your-secret-key-here
```

---

## 8. 开发计划

### 8.1 Phase 1: 核心功能（第1-2周）
- [x] 项目结构搭建
- [ ] 企业微信客户端实现
- [ ] 消息加解密实现
- [ ] 数据库模型和迁移
- [ ] 基础API接口

### 8.2 Phase 2: 消息处理（第3周）
- [ ] 消息解析器
- [ ] 命令管理器
- [ ] 消息处理服务
- [ ] 菜单管理

### 8.3 Phase 3: 前端开发（第4周）
- [ ] 配置页面
- [ ] 消息历史页面
- [ ] 命令管理页面
- [ ] 仪表盘

### 8.4 Phase 4: 部署和测试（第5周）
- [ ] Docker镜像构建
- [ ] 部署文档
- [ ] 功能测试
- [ ] 性能优化

---

## 9. 关键技术点

### 9.1 消息加解密
- 使用 AES-256-CBC 加密
- PKCS7 填充
- Base64 编码
- SHA1 签名验证

### 9.2 Access Token 管理
- 内存缓存（7200秒有效期）
- 自动刷新机制
- 并发请求防重

### 9.3 消息分块
- 单条消息最大 2048 字节
- 自动分块发送
- 保持消息顺序

### 9.4 错误处理
- API错误码映射
- 自动重试机制（指数退避）
- 详细错误日志

---

## 10. 安全考虑

### 10.1 消息验证
- 签名验证（msg_signature）
- 时间戳验证（防重放攻击）
- 白名单机制

### 10.2 配置安全
- 敏感信息加密存储
- 环境变量注入
- 配置文件权限控制

### 10.3 API安全
- HTTPS强制
- CORS配置
- 速率限制

---

## 11. 扩展性设计

### 11.1 命令插件化
```python
# 支持动态加载命令
class CommandPlugin:
    def register(self, manager: CommandManager):
        """注册命令到管理器"""
```

### 11.2 消息处理器链
```python
# 支持多个处理器串联
class MessageHandler:
    async def handle(self, message: Message) -> Optional[Message]:
        """处理消息，返回None表示终止链"""
```

### 11.3 多租户支持
- 支持多个企业微信应用配置
- 配置隔离
- 消息路由

---

## 12. 参考资料

- [企业微信API文档](https://developer.work.weixin.qq.com/document/)
- [消息加解密说明](https://developer.work.weixin.qq.com/document/path/90968)
- [应用菜单配置](https://developer.work.weixin.qq.com/document/path/90231)
- MoviePilot 源码分析（见前文）

---

## 附录A: MoviePilot代码迁移清单

### A.1 需要迁移的文件
```
MoviePilot-2/app/modules/wechat/
├── wechat.py              → backend/app/services/wechat/client.py
├── WXBizMsgCrypt3.py      → backend/app/services/wechat/crypto.py
└── __init__.py            → backend/app/services/wechat/parser.py

MoviePilot-2/app/api/endpoints/
└── message.py             → backend/app/api/endpoints/wechat.py

MoviePilot-2/app/db/models/
└── message.py             → backend/app/models/message.py

MoviePilot-Frontend-2/src/views/setting/
└── AccountSettingNotification.vue → frontend/src/views/Config.vue
```

### A.2 需要删除的功能
- 媒体库管理
- 下载器集成
- 订阅管理
- AI Agent
- 插件系统
- 站点管理
- 刮削器
- 定时任务（保留基础调度）

### A.3 需要简化的模块
- 数据库：只保留消息、配置、命令表
- API：只保留企业微信相关接口
- 前端：只保留配置和消息管理页面

---

## 附录B: 快速开始指南

### B.1 开发环境搭建
```bash
# 克隆代码
git clone <repo-url>
cd wecom-cmder

# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

### B.2 Docker部署
```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

### B.3 企业微信配置
1. 登录企业微信管理后台
2. 创建自建应用
3. 获取 CorpID、AgentId、Secret
4. 配置回调URL: `https://your-domain/api/v1/wechat/callback`
5. 生成 Token 和 EncodingAESKey
6. 在系统配置页面填入以上信息
7. 点击"测试配置"验证

---

**文档版本**: v1.0
**创建日期**: 2026-01-30
**最后更新**: 2026-01-30
**作者**: Claude Code
**状态**: 待审核
