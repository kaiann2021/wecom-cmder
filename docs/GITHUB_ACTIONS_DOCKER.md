# GitHub Actions Docker 构建配置

## 概述

本项目配置了 GitHub Actions 工作流，用于自动构建 Docker 镜像并推送到 GitHub Container Registry (ghcr.io)。

## 功能特性

- ✅ 自动构建 backend 和 frontend 两个 Docker 镜像
- ✅ 支持多架构构建（amd64 和 arm64）
- ✅ 推送代码到 main/master 分支时自动触发
- ✅ 创建 Git tag 时自动构建带版本号的镜像
- ✅ 支持手动触发构建
- ✅ 使用 GitHub Actions 缓存加速构建

## 镜像标签策略

### 分支推送
推送到 `main` 或 `master` 分支时：
- `ghcr.io/<username>/<repo>/backend:latest`
- `ghcr.io/<username>/<repo>/frontend:latest`
- `ghcr.io/<username>/<repo>/backend:main`
- `ghcr.io/<username>/<repo>/frontend:main`

### 版本标签
创建版本标签（如 `v1.0.0`）时：
- `ghcr.io/<username>/<repo>/backend:v1.0.0`
- `ghcr.io/<username>/<repo>/backend:1.0.0`
- `ghcr.io/<username>/<repo>/backend:1.0`
- `ghcr.io/<username>/<repo>/backend:1`
- `ghcr.io/<username>/<repo>/frontend:v1.0.0`
- `ghcr.io/<username>/<repo>/frontend:1.0.0`
- `ghcr.io/<username>/<repo>/frontend:1.0`
- `ghcr.io/<username>/<repo>/frontend:1`

### Commit SHA
每次提交都会生成基于 SHA 的标签：
- `ghcr.io/<username>/<repo>/backend:main-abc1234`
- `ghcr.io/<username>/<repo>/frontend:main-abc1234`

## 使用构建的镜像

### 1. 设置镜像为公开（可选）

默认情况下，推送到 GHCR 的镜像是私有的。要使其公开：

1. 访问 `https://github.com/<username>/<repo>/packages`
2. 选择 package（backend 或 frontend）
3. 点击 "Package settings"
4. 在 "Danger Zone" 中选择 "Change visibility" → "Public"

### 2. 拉取镜像

```bash
# 拉取 backend 最新版本
docker pull ghcr.io/<username>/<repo>/backend:latest

# 拉取 frontend 最新版本
docker pull ghcr.io/<username>/<repo>/frontend:latest

# 拉取特定版本
docker pull ghcr.io/<username>/<repo>/backend:v1.0.0
```

### 3. 使用 docker-compose

修改 `docker-compose.yml` 使用预构建的镜像：

```yaml
version: '3.8'

services:
  backend:
    image: ghcr.io/<username>/<repo>/backend:latest
    # 移除 build 配置
    container_name: wecom-cmder-backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - TZ=Asia/Shanghai
      - DATABASE_URL=sqlite:///data/wecom.db
      - LOG_LEVEL=INFO
      - CORS_ORIGINS=http://localhost:3000,http://localhost
    restart: unless-stopped

  frontend:
    image: ghcr.io/<username>/<repo>/frontend:latest
    # 移除 build 配置
    container_name: wecom-cmder-frontend
    ports:
      - "3000:80"
    environment:
      - TZ=Asia/Shanghai
    depends_on:
      - backend
    restart: unless-stopped
```

### 4. 私有镜像认证

如果镜像是私有的，需要先登录：

```bash
# 使用 Personal Access Token (PAT)
echo $GITHUB_TOKEN | docker login ghcr.io -u <username> --password-stdin

# 或者使用交互式登录
docker login ghcr.io
```

创建 Personal Access Token：
1. 访问 `https://github.com/settings/tokens`
2. 点击 "Generate new token (classic)"
3. 选择权限：`read:packages`
4. 生成并复制 token

## 手动触发构建

1. 访问仓库的 Actions 页面
2. 选择 "Build and Push Docker Images" workflow
3. 点击 "Run workflow"
4. 选择分支
5. 点击 "Run workflow" 按钮

## 发布新版本

使用 Git tags 发布新版本：

```bash
# 创建版本标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 推送标签到远程仓库
git push origin v1.0.0

# GitHub Actions 会自动构建并推送带版本号的镜像
```

## 工作流配置文件

配置文件位置：`.github/workflows/docker-build.yml`

主要配置：
- **触发条件**：推送到 main/master 分支、创建 tag、手动触发
- **构建平台**：linux/amd64, linux/arm64
- **缓存**：使用 GitHub Actions 缓存加速构建
- **权限**：需要 `contents: read` 和 `packages: write`

## 查看构建状态

在仓库的 README.md 中添加构建徽章：

```markdown
![Docker Build](https://github.com/<username>/<repo>/actions/workflows/docker-build.yml/badge.svg)
```

## 常见问题

### Q: 构建失败，提示权限错误
A: 确保仓库设置中启用了 GitHub Actions 的写入权限：
- 访问 `Settings` → `Actions` → `General`
- 在 "Workflow permissions" 中选择 "Read and write permissions"

### Q: 如何查看已推送的镜像
A: 访问 `https://github.com/<username>/<repo>/packages`

### Q: 如何删除旧的镜像版本
A: 
1. 访问 package 页面
2. 点击右侧的版本号
3. 点击 "Delete version"

### Q: PR 会推送镜像吗？
A: 不会。Pull Request 只会构建镜像但不推送，用于验证构建是否成功。

## 安全建议

1. **不要在镜像中包含敏感信息**（密码、密钥等）
2. **使用环境变量**传递配置信息
3. **定期更新基础镜像**以获取安全补丁
4. **启用 Dependabot** 自动更新依赖
5. **私有仓库的镜像默认是私有的**，确保敏感项目不要设为公开

## 优化建议

1. **多阶段构建**：减小最终镜像大小（已在 Dockerfile 中实现）
2. **层缓存**：合理排列 Dockerfile 指令顺序
3. **并行构建**：backend 和 frontend 独立并行构建
4. **条件推送**：PR 不推送镜像，节省存储空间

## 参考资源

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [GitHub Container Registry 文档](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker 多架构构建](https://docs.docker.com/build/building/multi-platform/)
