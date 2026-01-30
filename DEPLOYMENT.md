# Linux 服务器部署指南

## 环境要求

### 系统要求
- **操作系统**: Ubuntu 20.04+ / CentOS 7+ / Debian 10+
- **CPU**: 2核心以上
- **内存**: 2GB 以上
- **磁盘**: 10GB 以上可用空间
- **网络**: 公网 IP 或域名（用于企业微信回调）

### 软件要求
- Docker 20.10+
- Docker Compose 2.0+
- Git（可选，用于代码拉取）

---

## 部署步骤

### 1. 安装 Docker 和 Docker Compose

#### Ubuntu/Debian

```bash
# 更新包索引
sudo apt-get update

# 安装必要的包
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 添加 Docker 官方 GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 设置稳定版仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
sudo docker --version
sudo docker compose version
```

#### CentOS/RHEL

```bash
# 安装必要的包
sudo yum install -y yum-utils

# 添加 Docker 仓库
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 安装 Docker Engine
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
sudo docker --version
sudo docker compose version
```

#### 配置 Docker 用户权限（可选）

```bash
# 将当前用户添加到 docker 组
sudo usermod -aG docker $USER

# 重新登录或执行
newgrp docker

# 验证（不需要 sudo）
docker ps
```

---

### 2. 上传代码到服务器

#### 方式一：使用 Git（推荐）

```bash
# 在服务器上克隆代码
cd /opt
sudo git clone https://github.com/kaiann2021/wecom-cmder.git wecom-cmder
cd wecom-cmder
```

#### 方式二：使用 SCP 上传

```bash
# 在本地执行（Windows 使用 PowerShell 或 Git Bash）
scp -r D:\code\wecom-cmder user@your-server-ip:/opt/

# 在服务器上
cd /opt/wecom-cmder
```

#### 方式三：使用 SFTP 工具
- 使用 FileZilla、WinSCP 等工具上传整个项目目录

---

### 3. 配置环境变量

创建生产环境配置文件：

```bash
cd /opt/wecom-cmder

# 创建 .env 文件
cat > .env << 'EOF'
# 数据库配置
DATABASE_URL=sqlite:///data/wecom.db

# 日志级别
LOG_LEVEL=INFO

# CORS 配置（替换为你的实际域名）
CORS_ORIGINS=https://your-domain.com,http://your-domain.com

# JWT 密钥（可选）
SECRET_KEY=your-secret-key-here-change-this-in-production
EOF

# 设置文件权限
chmod 600 .env
```

---

### 4. 修改 docker-compose.yml（生产环境）

创建生产环境的 docker-compose 配置：

```bash
# 备份原配置
cp docker-compose.yml docker-compose.dev.yml

# 创建生产配置
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  backend:
    build: ./backend
    container_name: wecom-cmder-backend
    ports:
      - "127.0.0.1:8000:8000"  # 只监听本地，通过 nginx 代理
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    env_file:
      - .env
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "python -c 'import urllib.request; urllib.request.urlopen(\"http://localhost:8000/health\")'"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  frontend:
    build: ./frontend
    container_name: wecom-cmder-frontend
    ports:
      - "127.0.0.1:3000:80"  # 只监听本地，通过 nginx 代理
    depends_on:
      - backend
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  data:
    driver: local
EOF
```

---

### 5. 构建和启动服务

```bash
cd /opt/wecom-cmder

# 创建必要的目录
mkdir -p data logs

# 构建镜像
docker compose -f docker-compose.prod.yml build

# 启动服务
docker compose -f docker-compose.prod.yml up -d

# 查看服务状态
docker compose -f docker-compose.prod.yml ps

# 查看日志
docker compose -f docker-compose.prod.yml logs -f
```

---

### 6. 配置 Nginx 反向代理（推荐）

#### 安装 Nginx

```bash
# Ubuntu/Debian
sudo apt-get install -y nginx

# CentOS/RHEL
sudo yum install -y nginx

# 启动 Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

#### 配置反向代理

```bash
# 创建配置文件
sudo nano /etc/nginx/sites-available/wecom-cmder

# 或者使用 vim
sudo vim /etc/nginx/sites-available/wecom-cmder
```

**HTTP 配置（测试用）：**

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名或 IP

    # 日志
    access_log /var/log/nginx/wecom-cmder-access.log;
    error_log /var/log/nginx/wecom-cmder-error.log;

    # 前端
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000;
    }

    # API 文档
    location /docs {
        proxy_pass http://127.0.0.1:8000;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

**HTTPS 配置（生产环境推荐）：**

```nginx
# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS 配置
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书（使用 Let's Encrypt 或其他证书）
    ssl_certificate /etc/nginx/ssl/your-domain.crt;
    ssl_certificate_key /etc/nginx/ssl/your-domain.key;

    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 日志
    access_log /var/log/nginx/wecom-cmder-access.log;
    error_log /var/log/nginx/wecom-cmder-error.log;

    # 前端
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000;
    }

    # API 文档
    location /docs {
        proxy_pass http://127.0.0.1:8000;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

#### 启用配置

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/wecom-cmder /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

---

### 7. 配置 SSL 证书（使用 Let's Encrypt）

```bash
# 安装 Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期（Certbot 会自动配置）
sudo certbot renew --dry-run
```

---

### 8. 配置防火墙

```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

---

### 9. 验证部署

```bash
# 检查服务状态
docker compose -f docker-compose.prod.yml ps

# 检查健康状态
curl http://localhost:8000/health

# 检查前端
curl http://localhost:3000

# 通过域名访问
curl https://your-domain.com/health
```

---

### 10. 配置企业微信

1. 访问 `https://your-domain.com/config`
2. 填写企业微信配置信息
3. 设置回调URL: `https://your-domain.com/api/v1/wechat/callback`
4. 测试配置
5. 保存并同步菜单

---

## 运维管理

### 查看日志

```bash
# 查看所有服务日志
docker compose -f docker-compose.prod.yml logs -f

# 查看后端日志
docker compose -f docker-compose.prod.yml logs -f backend

# 查看前端日志
docker compose -f docker-compose.prod.yml logs -f frontend

# 查看 Nginx 日志
sudo tail -f /var/log/nginx/wecom-cmder-access.log
sudo tail -f /var/log/nginx/wecom-cmder-error.log
```

### 重启服务

```bash
# 重启所有服务
docker compose -f docker-compose.prod.yml restart

# 重启后端
docker compose -f docker-compose.prod.yml restart backend

# 重启前端
docker compose -f docker-compose.prod.yml restart frontend
```

### 更新代码

```bash
cd /opt/wecom-cmder

# 拉取最新代码
git pull

# 重新构建并启动
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# 清理旧镜像
docker image prune -f
```

### 备份数据

```bash
# 备份数据库
cp /opt/wecom-cmder/data/wecom.db /backup/wecom-$(date +%Y%m%d).db

# 或使用定时任务
crontab -e

# 添加每天凌晨2点备份
0 2 * * * cp /opt/wecom-cmder/data/wecom.db /backup/wecom-$(date +\%Y\%m\%d).db
```

### 监控服务

```bash
# 查看资源使用
docker stats

# 查看容器状态
docker compose -f docker-compose.prod.yml ps

# 设置自动重启
# 已在 docker-compose.prod.yml 中配置 restart: always
```

---

## 故障排查

### 服务无法启动

```bash
# 查看详细日志
docker compose -f docker-compose.prod.yml logs

# 检查端口占用
sudo netstat -tulpn | grep -E ':(80|443|3000|8000)'

# 检查磁盘空间
df -h

# 检查 Docker 状态
sudo systemctl status docker
```

### 企业微信回调失败

1. 检查回调URL是否可以从公网访问
2. 检查 SSL 证书是否有效
3. 检查 Token 和 EncodingAESKey 配置
4. 查看后端日志

```bash
docker compose -f docker-compose.prod.yml logs backend | grep -i wechat
```

### 数据库问题

```bash
# 进入容器
docker exec -it wecom-cmder-backend bash

# 检查数据库文件
ls -lh /app/data/

# 查看数据库
python -c "from app.core.database import engine; print(engine.table_names())"
```

---

## 安全建议

1. **定期更新系统和 Docker**
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```

2. **限制 SSH 访问**
   - 使用密钥认证
   - 禁用 root 登录
   - 修改默认端口

3. **配置防火墙**
   - 只开放必要的端口（80, 443）
   - 限制 SSH 访问源 IP

4. **定期备份**
   - 数据库文件
   - 配置文件
   - 日志文件

5. **监控日志**
   - 定期检查错误日志
   - 设置告警通知

---

## 性能优化

1. **数据库优化**
   - 考虑使用 PostgreSQL 替代 SQLite
   - 定期清理旧消息

2. **缓存优化**
   - 考虑使用 Redis 缓存 Access Token
   - 启用 Nginx 缓存

3. **资源限制**
   ```yaml
   # 在 docker-compose.prod.yml 中添加
   services:
     backend:
       deploy:
         resources:
           limits:
             cpus: '1.0'
             memory: 512M
   ```

---

## 快速部署脚本

创建一键部署脚本：

```bash
cat > deploy.sh << 'EOF'
#!/bin/bash

set -e

echo "==================================="
echo "WeCom Commander 部署脚本"
echo "==================================="

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "错误: 未安装 Docker"
    exit 1
fi

# 创建目录
mkdir -p data logs

# 构建镜像
echo "构建 Docker 镜像..."
docker compose -f docker-compose.prod.yml build

# 启动服务
echo "启动服务..."
docker compose -f docker-compose.prod.yml up -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查状态
echo "检查服务状态..."
docker compose -f docker-compose.prod.yml ps

echo "==================================="
echo "部署完成！"
echo "前端: http://localhost:3000"
echo "API: http://localhost:8000/docs"
echo "==================================="
EOF

chmod +x deploy.sh
```

使用：
```bash
./deploy.sh
```

---

## 总结

部署完成后，您应该能够：

1. ✅ 通过域名访问 Web 界面
2. ✅ 配置企业微信应用
3. ✅ 接收和发送消息
4. ✅ 管理命令和菜单
5. ✅ 查看消息历史

如有问题，请查看日志或参考故障排查章节。
