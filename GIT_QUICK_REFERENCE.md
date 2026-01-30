# Git 快速参考

## 仓库信息

- **仓库地址**: https://github.com/kaiann2021/wecom-cmder
- **SSH Host**: prv
- **SSH URL**: prv:kaiann2021/wecom-cmder.git
- **HTTPS URL**: https://github.com/kaiann2021/wecom-cmder.git

---

## 快速开始

### 初始化仓库（首次）

**Windows:**
```cmd
git-init.bat
```

**Linux/Mac:**
```bash
chmod +x git-init.sh
./git-init.sh
```

### 手动初始化

```bash
# 1. 初始化 Git
git init

# 2. 添加远程仓库（SSH）
git remote add origin prv:kaiann2021/wecom-cmder.git

# 或使用 HTTPS
git remote add origin https://github.com/kaiann2021/wecom-cmder.git

# 3. 添加文件
git add .

# 4. 首次提交
git commit -m "Initial commit: WeCom Commander v1.0.0"

# 5. 推送
git branch -M main
git push -u origin main
```

---

## 日常操作

### 提交代码

```bash
# 查看状态
git status

# 添加修改
git add .

# 提交
git commit -m "描述你的修改"

# 推送
git push
```

### 拉取更新

```bash
# 拉取最新代码
git pull

# 或使用 rebase
git pull --rebase
```

### 查看历史

```bash
# 查看提交历史
git log --oneline --graph --all

# 查看最近 10 条
git log --oneline -10

# 查看某个文件的历史
git log --follow -- <file>
```

---

## 分支操作

### 创建分支

```bash
# 创建并切换到新分支
git checkout -b feature/new-feature

# 推送新分支
git push -u origin feature/new-feature
```

### 切换分支

```bash
# 切换到已存在的分支
git checkout main

# 或使用新命令
git switch main
```

### 合并分支

```bash
# 切换到目标分支
git checkout main

# 合并其他分支
git merge feature/new-feature

# 推送
git push
```

### 删除分支

```bash
# 删除本地分支
git branch -d feature/old-feature

# 强制删除
git branch -D feature/old-feature

# 删除远程分支
git push origin --delete feature/old-feature
```

---

## 撤销操作

### 撤销工作区修改

```bash
# 撤销单个文件
git checkout -- <file>

# 撤销所有修改
git checkout -- .
```

### 撤销暂存区

```bash
# 取消暂存单个文件
git reset HEAD <file>

# 取消所有暂存
git reset HEAD .
```

### 撤销提交

```bash
# 撤销最后一次提交（保留修改）
git reset --soft HEAD^

# 撤销最后一次提交（不保留修改）
git reset --hard HEAD^

# 撤销并创建新提交
git revert HEAD
```

---

## 标签管理

### 创建标签

```bash
# 创建轻量标签
git tag v1.0.0

# 创建附注标签
git tag -a v1.0.0 -m "Release v1.0.0"

# 推送标签
git push origin v1.0.0

# 推送所有标签
git push origin --tags
```

### 删除标签

```bash
# 删除本地标签
git tag -d v1.0.0

# 删除远程标签
git push origin --delete v1.0.0
```

---

## 常见问题

### SSH 连接失败

```bash
# 测试 SSH 连接
ssh -T prv

# 查看详细信息
ssh -vT prv

# 添加 SSH 密钥
ssh-add ~/.ssh/id_rsa_github
```

### 推送被拒绝

```bash
# 拉取远程更新
git pull --rebase origin main

# 然后推送
git push
```

### 查看忽略的文件

```bash
# 查看被忽略的文件
git status --ignored

# 检查某个文件是否被忽略
git check-ignore -v <file>
```

### 清理未跟踪的文件

```bash
# 查看将被删除的文件
git clean -n

# 删除未跟踪的文件
git clean -f

# 删除未跟踪的文件和目录
git clean -fd
```

---

## 提交信息规范

### 约定式提交（Conventional Commits）

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型（type）

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式（不影响代码运行）
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试
- `chore`: 构建过程或辅助工具的变动

### 示例

```bash
# 新功能
git commit -m "feat: 添加消息推送功能"

# 修复 bug
git commit -m "fix: 修复企业微信回调验证失败的问题"

# 文档更新
git commit -m "docs: 更新部署文档"

# 重构
git commit -m "refactor: 重构消息处理服务"
```

---

## 配置

### 用户信息

```bash
# 设置用户名
git config --global user.name "Your Name"

# 设置邮箱
git config --global user.email "your.email@example.com"

# 查看配置
git config --list
```

### 别名

```bash
# 设置别名
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.lg "log --oneline --graph --all"

# 使用别名
git st
git lg
```

---

## 有用的命令

```bash
# 查看远程仓库
git remote -v

# 查看分支
git branch -a

# 查看差异
git diff

# 查看暂存区差异
git diff --staged

# 查看文件修改历史
git log -p <file>

# 查看谁修改了某行代码
git blame <file>

# 搜索提交信息
git log --grep="关键词"

# 搜索代码
git log -S "代码片段"
```

---

## 参考资料

- Git 官方文档: https://git-scm.com/doc
- GitHub 文档: https://docs.github.com/
- 约定式提交: https://www.conventionalcommits.org/
- Git 教程: https://www.atlassian.com/git/tutorials
