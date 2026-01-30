# GitHub Actions + Docker 快速参考

## 🚀 首次设置

### 1. 启用 GitHub Actions 写权限

在仓库设置中启用：
1. 访问 `Settings` → `Actions` → `General`
2. 在 "Workflow permissions" 中选择 **"Read and write permissions"**
3. 勾选 **"Allow GitHub Actions to create and approve pull requests"**
4. 点击 **Save**

### 2. 推送代码触发构建

```bash
git add .
git commit -m "feat: add GitHub Actions workflow"
git push origin main
```

构建将自动开始，可在 `Actions` 标签页查看进度。

### 3. 设置镜像为公开（可选）

如果希望任何人都能拉取镜像：

1. 访问 `https://github.com/YOUR_USERNAME/wecom-cmder/packages`
2. 点击 `backend` 或 `frontend` package
3. 点击右上角 **Package settings**
4. 滚动到底部 "Danger Zone"
5. 点击 **Change visibility** → **Public**
6. 输入仓库名称确认

## 📦 使用镜像

### 拉取最新版本

```bash
docker pull ghcr.io/YOUR_USERNAME/wecom-cmder/backend:latest
docker pull ghcr.io/YOUR_USERNAME/wecom-cmder/frontend:latest
```

### 拉取特定版本

```bash
docker pull ghcr.io/YOUR_USERNAME/wecom-cmder/backend:v1.0.0
docker pull ghcr.io/YOUR_USERNAME/wecom-cmder/frontend:v1.0.0
```

### 使用 docker-compose

创建 `docker-compose.override.yml`：

```yaml
version: '3.8'

services:
  backend:
    image: ghcr.io/YOUR_USERNAME/wecom-cmder/backend:latest
    build: null
  
  frontend:
    image: ghcr.io/YOUR_USERNAME/wecom-cmder/frontend:latest
    build: null
```

然后启动：

```bash
docker-compose up -d
```

## 🏷️ 发布版本

### 创建版本标签

```bash
# 创建并推送标签
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

这将自动构建以下镜像：
- `ghcr.io/YOUR_USERNAME/wecom-cmder/backend:v1.0.0`
- `ghcr.io/YOUR_USERNAME/wecom-cmder/backend:1.0.0`
- `ghcr.io/YOUR_USERNAME/wecom-cmder/backend:1.0`
- `ghcr.io/YOUR_USERNAME/wecom-cmder/backend:1`
- （frontend 同理）

### 列出所有标签

```bash
git tag -l
```

### 删除标签

```bash
# 删除本地标签
git tag -d v1.0.0

# 删除远程标签
git push origin :refs/tags/v1.0.0
```

## 🔐 私有镜像认证

如果镜像是私有的，需要先登录：

### 方法一：使用 GitHub Token

```bash
# 创建 Personal Access Token (经典)
# 访问: https://github.com/settings/tokens
# 权限: read:packages

# 登录
echo YOUR_GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin
```

### 方法二：交互式登录

```bash
docker login ghcr.io
# Username: YOUR_USERNAME
# Password: YOUR_GITHUB_TOKEN
```

## 🔄 手动触发构建

1. 访问仓库的 **Actions** 页面
2. 选择左侧的 **"Build and Push Docker Images"**
3. 点击右侧的 **"Run workflow"** 按钮
4. 选择分支（默认 main）
5. 点击绿色的 **"Run workflow"** 按钮

## 📊 查看构建状态

### 在 README 中添加徽章

```markdown
![Docker Build](https://github.com/YOUR_USERNAME/wecom-cmder/actions/workflows/docker-build.yml/badge.svg)
```

效果：
![Docker Build](https://github.com/YOUR_USERNAME/wecom-cmder/actions/workflows/docker-build.yml/badge.svg)

### 查看构建历史

访问：`https://github.com/YOUR_USERNAME/wecom-cmder/actions`

## 🗑️ 管理镜像

### 查看所有镜像版本

访问：`https://github.com/YOUR_USERNAME/wecom-cmder/packages`

### 删除特定版本

1. 进入 package 页面
2. 点击版本号
3. 点击右上角 **Delete version**
4. 确认删除

### 批量删除（使用 GitHub CLI）

```bash
# 安装 GitHub CLI
# https://cli.github.com/

# 登录
gh auth login

# 列出所有版本
gh api -X GET /users/YOUR_USERNAME/packages/container/wecom-cmder%2Fbackend/versions

# 删除特定版本（替换 VERSION_ID）
gh api -X DELETE /users/YOUR_USERNAME/packages/container/wecom-cmder%2Fbackend/versions/VERSION_ID
```

## 📝 常用命令速查

```bash
# 拉取镜像
docker pull ghcr.io/YOUR_USERNAME/wecom-cmder/backend:latest

# 查看本地镜像
docker images | grep wecom-cmder

# 删除本地镜像
docker rmi ghcr.io/YOUR_USERNAME/wecom-cmder/backend:latest

# 启动服务（使用预构建镜像）
docker-compose up -d

# 重新拉取最新镜像并重启
docker-compose pull
docker-compose up -d

# 查看日志
docker-compose logs -f backend

# 停止服务
docker-compose down

# 停止并删除卷
docker-compose down -v
```

## ⚠️ 故障排查

### 问题：Actions 权限错误

**错误信息**：`Error: failed to push: insufficient_scope`

**解决方案**：
1. 检查 Settings → Actions → General
2. 确保选择了 "Read and write permissions"

### 问题：镜像拉取失败

**错误信息**：`Error response from daemon: pull access denied`

**解决方案**：
1. 如果镜像是私有的，先执行 `docker login ghcr.io`
2. 检查镜像名称是否正确
3. 检查 token 权限（需要 `read:packages`）

### 问题：多架构构建失败

**错误信息**：`ERROR: failed to solve: process "/bin/sh -c ..."`

**解决方案**：
1. 检查 Dockerfile 中的命令是否兼容 arm64
2. 某些软件包可能不支持 arm64，考虑只构建 amd64：
   ```yaml
   platforms: linux/amd64  # 移除 linux/arm64
   ```

## 📚 更多资源

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [GHCR 文档](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker Buildx 文档](https://docs.docker.com/build/buildx/)
- [详细说明文档](./GITHUB_ACTIONS_DOCKER.md)

## 🎯 最佳实践

1. ✅ **使用版本标签**管理发布
2. ✅ **多架构支持**（amd64 + arm64）
3. ✅ **利用缓存**加速构建
4. ✅ **分离后端和前端**镜像
5. ✅ **定期清理**旧版本镜像
6. ✅ **使用 .dockerignore** 减小上下文大小
7. ✅ **PR 不推送镜像**，只验证构建
