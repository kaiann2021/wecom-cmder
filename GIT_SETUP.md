# Git 仓库配置指南

## 仓库信息

- **仓库地址**: https://github.com/kaiann2021/wecom-cmder
- **SSH Host**: prv（需要在 SSH 配置中设置）

---

## 1. 配置 SSH（使用 Host 别名 prv）

### 编辑 SSH 配置文件

**Windows**: `C:\Users\你的用户名\.ssh\config`
**Linux/Mac**: `~/.ssh/config`

```ssh
# GitHub 配置（使用 prv 别名）
Host prv
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_rsa_github
    # 或者使用你的 GitHub SSH 密钥路径
```

### 测试 SSH 连接

```bash
ssh -T prv
# 应该看到: Hi kaiann2021! You've successfully authenticated...
```

---

## 2. 初始化 Git 仓库

### 在项目目录执行

```bash
cd D:\code\wecom-cmder

# 初始化 Git 仓库
git init

# 添加远程仓库（使用 prv Host）
git remote add origin prv:kaiann2021/wecom-cmder.git

# 或者使用 HTTPS（如果不用 SSH）
# git remote add origin https://github.com/kaiann2021/wecom-cmder.git

# 查看远程仓库配置
git remote -v
```

---

## 3. 首次提交

### 检查要提交的文件

```bash
# 查看状态
git status

# 查看将被忽略的文件
git status --ignored

# 确认 MoviePilot 相关目录已被忽略
git check-ignore -v MoviePilot-2/
git check-ignore -v MoviePilot-Frontend-2/
git check-ignore -v MoviePilot-Resources/
```

### 添加文件并提交

```bash
# 添加所有文件（.gitignore 会自动排除不需要的文件）
git add .

# 查看将要提交的文件
git status

# 创建首次提交
git commit -m "Initial commit: WeCom Commander v1.0.0

- 完整的后端实现（FastAPI + Python）
- 现代化前端界面（Vue 3 + TypeScript + Vuetify）
- Docker 容器化部署
- 企业微信集成（消息推送、指令接收、菜单交互）
- 完善的部署文档

基于 MoviePilot 项目精简而来，专注于企业微信功能。"
```

---

## 4. 推送到 GitHub

### 首次推送

```bash
# 推送到 main 分支（GitHub 默认分支）
git branch -M main
git push -u origin main

# 如果遇到错误，可能需要先拉取
# git pull origin main --allow-unrelated-histories
# git push -u origin main
```

### 后续推送

```bash
# 添加修改
git add .

# 提交
git commit -m "描述你的修改"

# 推送
git push
```

---

## 5. 创建 .gitattributes（可选）

为了确保跨平台一致性，建议创建 .gitattributes 文件：

```bash
# 创建 .gitattributes
cat > .gitattributes << 'EOF'
# Auto detect text files and perform LF normalization
* text=auto

# Shell scripts
*.sh text eol=lf

# Python files
*.py text eol=lf

# JavaScript/TypeScript files
*.js text eol=lf
*.ts text eol=lf
*.vue text eol=lf
*.json text eol=lf

# Markdown files
*.md text eol=lf

# Docker files
Dockerfile text eol=lf
docker-compose*.yml text eol=lf

# Config files
*.yml text eol=lf
*.yaml text eol=lf
*.toml text eol=lf
*.ini text eol=lf

# Binary files
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.ico binary
*.db binary
*.sqlite binary
EOF

# 添加到 Git
git add .gitattributes
git commit -m "Add .gitattributes for cross-platform consistency"
git push
```

---

## 6. 分支管理建议

### 创建开发分支

```bash
# 创建并切换到开发分支
git checkout -b develop

# 推送开发分支
git push -u origin develop
```

### 分支策略

```
main (生产环境)
  ↑
develop (开发环境)
  ↑
feature/* (功能分支)
```

---

## 7. 常用 Git 命令

### 查看状态

```bash
# 查看当前状态
git status

# 查看提交历史
git log --oneline --graph --all

# 查看远程仓库
git remote -v
```

### 撤销操作

```bash
# 撤销工作区修改
git checkout -- <file>

# 撤销暂存区
git reset HEAD <file>

# 撤销最后一次提交（保留修改）
git reset --soft HEAD^

# 撤销最后一次提交（不保留修改）
git reset --hard HEAD^
```

### 更新代码

```bash
# 拉取最新代码
git pull

# 拉取并变基
git pull --rebase
```

---

## 8. GitHub 仓库设置建议

### 在 GitHub 网页上设置

1. **添加 README.md**
   - 已包含在项目中

2. **设置 Topics**
   - wechat
   - enterprise-wechat
   - fastapi
   - vue3
   - docker
   - python
   - typescript

3. **添加 License**
   - 建议使用 MIT License

4. **设置 Branch Protection**
   - 保护 main 分支
   - 要求 PR 审查
   - 要求状态检查通过

5. **配置 GitHub Actions**（可选）
   - 自动构建 Docker 镜像
   - 运行测试
   - 代码质量检查

---

## 9. 创建 Release

### 创建标签

```bash
# 创建标签
git tag -a v1.0.0 -m "Release v1.0.0

- 完整的企业微信指令管理系统
- 后端 + 前端 + Docker 部署
- 生产就绪"

# 推送标签
git push origin v1.0.0

# 推送所有标签
git push origin --tags
```

### 在 GitHub 上创建 Release

1. 访问 https://github.com/kaiann2021/wecom-cmder/releases
2. 点击 "Create a new release"
3. 选择标签 v1.0.0
4. 填写 Release 标题和说明
5. 上传构建产物（可选）
6. 发布

---

## 10. 故障排查

### SSH 连接问题

```bash
# 测试 SSH 连接
ssh -T prv

# 查看详细信息
ssh -vT prv

# 检查 SSH 密钥
ls -la ~/.ssh/

# 添加 SSH 密钥到 ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa_github
```

### 推送被拒绝

```bash
# 如果远程有更新
git pull --rebase origin main
git push

# 如果需要强制推送（谨慎使用）
git push -f origin main
```

### 文件过大

```bash
# 查看大文件
git rev-list --objects --all | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  awk '/^blob/ {print substr($0,6)}' | \
  sort --numeric-sort --key=2 | \
  tail -n 10

# 从历史中删除大文件
git filter-branch --tree-filter 'rm -f path/to/large/file' HEAD
```

---

## 11. 协作开发

### Fork 工作流

```bash
# 添加上游仓库
git remote add upstream prv:kaiann2021/wecom-cmder.git

# 同步上游更新
git fetch upstream
git merge upstream/main
```

### Pull Request 流程

1. Fork 仓库
2. 创建功能分支
3. 提交修改
4. 推送到 Fork 仓库
5. 创建 Pull Request
6. 代码审查
7. 合并到主分支

---

## 12. 快速命令参考

```bash
# 克隆仓库
git clone prv:kaiann2021/wecom-cmder.git

# 查看状态
git status

# 添加文件
git add .

# 提交
git commit -m "message"

# 推送
git push

# 拉取
git pull

# 查看日志
git log --oneline

# 查看分支
git branch -a

# 切换分支
git checkout branch-name

# 创建并切换分支
git checkout -b new-branch
```

---

## 注意事项

1. ✅ **确认 .gitignore 生效**
   - MoviePilot 相关目录不会被提交
   - data/ 和 logs/ 目录不会被提交
   - .env 文件不会被提交

2. ✅ **保护敏感信息**
   - 不要提交密钥、密码
   - 不要提交 SSL 证书
   - 不要提交数据库文件

3. ✅ **提交前检查**
   - 运行 `git status` 确认要提交的文件
   - 运行 `git diff` 查看修改内容
   - 确保没有调试代码

4. ✅ **提交信息规范**
   - 使用清晰的提交信息
   - 遵循约定式提交（Conventional Commits）
   - 例如：`feat:`, `fix:`, `docs:`, `refactor:`

---

## 完成确认

执行以下命令确认配置成功：

```bash
# 1. 检查 Git 配置
git config --list

# 2. 检查远程仓库
git remote -v

# 3. 检查 SSH 连接
ssh -T prv

# 4. 查看将要提交的文件
git status

# 5. 确认忽略规则
git check-ignore -v MoviePilot-2/
```

如果所有检查都通过，就可以执行首次提交和推送了！
