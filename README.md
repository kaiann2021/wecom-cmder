# WeCom Commander - 企业微信指令管理系统

基于 MoviePilot 项目精简而来，专注于企业微信集成功能，提供一个轻量级的企业微信指令管理和消息推送系统。

## 核心功能

1. **消息推送** - 发送文本、图片、卡片等消息到企业微信
2. **指令接收** - 接收企业微信消息并解析为程序指令
3. **菜单交互** - 配置和响应企业微信应用菜单
4. **OAuth认证** - 企业微信用户身份验证和授权（基础实现）

## 技术栈

- **后端**: Python 3.11 + FastAPI
- **前端**: Vue 3 + TypeScript + Vuetify（待实现）
- **数据库**: SQLite (可扩展为 PostgreSQL/MySQL)
- **容器化**: Docker + Docker Compose

## 快速开始

### 使用 Docker Compose（推荐）

```bash
# 克隆代码
git clone https://github.com/kaiann2021/wecom-cmder.git
cd wecom-cmder

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f backend

# 停止服务
docker-compose down
```

服务启动后：
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### 本地开发

#### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python -m app.main
# 或
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端开发（待实现）

```bash
cd frontend
npm install
npm run dev
```

## 企业微信配置

### 1. 创建企业微信应用

1. 登录 [企业微信管理后台](https://work.weixin.qq.com/)
2. 进入「应用管理」→「自建」→「创建应用」
3. 记录以下信息：
   - **企业ID (CorpID)**: 在「我的企业」→「企业信息」中查看
   - **应用AgentId**: 在应用详情页查看
   - **应用Secret**: 在应用详情页查看

### 2. 配置回调URL

1. 在应用详情页，进入「接收消息」设置
2. 设置回调URL: `https://your-domain/api/v1/wechat/callback`
3. 生成 **Token** 和 **EncodingAESKey**（点击「随机获取」）
4. 保存配置

### 3. 在系统中配置

#### 方式一：通过 API 配置

```bash
curl -X PUT http://localhost:8000/api/v1/config/wechat \
  -H "Content-Type: application/json" \
  -d '{
    "corp_id": "your_corp_id",
    "app_secret": "your_app_secret",
    "agent_id": "your_agent_id",
    "token": "your_token",
    "encoding_aes_key": "your_encoding_aes_key",
    "admin_users": ["user1", "user2"]
  }'
```

#### 方式二：通过前端界面配置（待实现）

访问配置页面，填写企业微信配置信息。

### 4. 测试配置

```bash
curl -X POST http://localhost:8000/api/v1/config/wechat/test \
  -H "Content-Type: application/json" \
  -d '{
    "corp_id": "your_corp_id",
    "app_secret": "your_app_secret",
    "agent_id": "your_agent_id"
  }'
```

### 5. 同步菜单

```bash
curl -X POST http://localhost:8000/api/v1/commands/sync-menu
```

## API 文档

启动服务后，访问 http://localhost:8000/docs 查看完整的 API 文档。

### 主要接口

#### 企业微信回调

- `GET /api/v1/wechat/callback` - URL验证
- `POST /api/v1/wechat/callback` - 接收消息

#### 配置管理

- `GET /api/v1/config/wechat` - 获取配置
- `PUT /api/v1/config/wechat` - 更新配置
- `POST /api/v1/config/wechat/test` - 测试配置

#### 消息管理

- `POST /api/v1/messages/send` - 发送消息
- `GET /api/v1/messages` - 获取消息历史

#### 命令管理

- `GET /api/v1/commands` - 获取命令列表
- `PUT /api/v1/commands/{command_id}` - 更新命令
- `POST /api/v1/commands/sync-menu` - 同步菜单

## 项目结构

```
wecom-cmder/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── api/               # API路由
│   │   │   ├── endpoints/     # 端点实现
│   │   │   └── router.py      # 路由注册
│   │   ├── core/              # 核心模块
│   │   │   └── database.py    # 数据库连接
│   │   ├── models/            # 数据模型
│   │   │   ├── message.py
│   │   │   ├── config.py
│   │   │   └── command.py
│   │   ├── schemas/           # Pydantic模型
│   │   ├── services/          # 业务逻辑
│   │   │   ├── wechat/        # 企业微信服务
│   │   │   ├── message.py     # 消息处理
│   │   │   └── command.py     # 命令处理
│   │   └── main.py            # 应用入口
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # 前端代码（待实现）
├── data/                       # 数据目录（SQLite数据库）
├── docker-compose.yml
└── README.md
```

## 开发指南

### 添加自定义命令

在 `backend/app/services/command.py` 中注册新命令：

```python
from app.services.command import command_manager, Command

# 定义命令处理函数
def handle_my_command(user_id: str, **kwargs) -> str:
    return f"Hello {user_id}!"

# 注册命令
command_manager.register_command(
    Command(
        id="my_command",
        name="我的命令",
        description="这是一个自定义命令",
        category="自定义",
        handler=handle_my_command,
        admin_only=False,
    )
)
```

### 数据库迁移

```bash
cd backend

# 创建迁移
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head
```

## 常见问题

### 1. 企业微信回调验证失败

- 检查 Token 和 EncodingAESKey 是否正确
- 确保回调URL可以从公网访问
- 查看后端日志获取详细错误信息

### 2. 消息发送失败

- 检查 CorpID、AppSecret、AgentId 是否正确
- 使用测试接口验证配置
- 查看企业微信应用的可见范围设置

### 3. 菜单不显示

- 确保已调用同步菜单接口
- 检查命令是否已启用
- 重新进入企业微信应用

## 许可证

MIT License

## 致谢

本项目基于 [MoviePilot](https://github.com/jxxghp/MoviePilot) 项目的企业微信模块精简而来，感谢原作者的贡献。

## 联系方式

- 问题反馈: [GitHub Issues](https://github.com/kaiann2021/wecom-cmder/issues)
- 技术文档: [Wiki](https://github.com/kaiann2021/wecom-cmder/wiki)
