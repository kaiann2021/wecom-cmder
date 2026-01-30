#!/bin/bash

# WeCom Commander Git 初始化脚本

set -e

echo "=================================="
echo "WeCom Commander Git 初始化"
echo "=================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 仓库信息
REPO_URL="prv:kaiann2021/wecom-cmder.git"
REPO_HTTPS="https://github.com/kaiann2021/wecom-cmder.git"

# 1. 检查 Git 是否安装
echo -e "${BLUE}1. 检查 Git 安装...${NC}"
if ! command -v git &> /dev/null; then
    echo -e "${RED}✗ Git 未安装${NC}"
    echo "请先安装 Git: https://git-scm.com/downloads"
    exit 1
fi
echo -e "${GREEN}✓ Git 已安装: $(git --version)${NC}"
echo ""

# 2. 检查是否已经是 Git 仓库
echo -e "${BLUE}2. 检查 Git 仓库状态...${NC}"
if [ -d ".git" ]; then
    echo -e "${YELLOW}⚠ 已经是 Git 仓库${NC}"
    echo "如需重新初始化，请先删除 .git 目录"
    read -p "是否继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
else
    echo -e "${GREEN}✓ 未初始化 Git 仓库${NC}"
fi
echo ""

# 3. 检查 SSH 配置
echo -e "${BLUE}3. 检查 SSH 配置...${NC}"
if ssh -T prv 2>&1 | grep -q "successfully authenticated"; then
    echo -e "${GREEN}✓ SSH 配置正确（使用 prv Host）${NC}"
    USE_SSH=true
else
    echo -e "${YELLOW}⚠ SSH 配置未找到或未配置${NC}"
    echo "将使用 HTTPS 方式"
    USE_SSH=false
fi
echo ""

# 4. 初始化 Git 仓库
echo -e "${BLUE}4. 初始化 Git 仓库...${NC}"
if [ ! -d ".git" ]; then
    git init
    echo -e "${GREEN}✓ Git 仓库初始化完成${NC}"
else
    echo -e "${YELLOW}⚠ Git 仓库已存在${NC}"
fi
echo ""

# 5. 配置远程仓库
echo -e "${BLUE}5. 配置远程仓库...${NC}"
if git remote | grep -q "origin"; then
    echo -e "${YELLOW}⚠ 远程仓库 origin 已存在${NC}"
    git remote -v
    read -p "是否更新远程仓库地址？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git remote remove origin
        if [ "$USE_SSH" = true ]; then
            git remote add origin "$REPO_URL"
        else
            git remote add origin "$REPO_HTTPS"
        fi
        echo -e "${GREEN}✓ 远程仓库已更新${NC}"
    fi
else
    if [ "$USE_SSH" = true ]; then
        git remote add origin "$REPO_URL"
        echo -e "${GREEN}✓ 远程仓库已添加（SSH）${NC}"
    else
        git remote add origin "$REPO_HTTPS"
        echo -e "${GREEN}✓ 远程仓库已添加（HTTPS）${NC}"
    fi
fi
git remote -v
echo ""

# 6. 检查要忽略的文件
echo -e "${BLUE}6. 检查 .gitignore 配置...${NC}"
if [ -f ".gitignore" ]; then
    echo -e "${GREEN}✓ .gitignore 文件存在${NC}"

    # 检查 MoviePilot 目录是否会被忽略
    if [ -d "MoviePilot-2" ]; then
        if git check-ignore -q MoviePilot-2/; then
            echo -e "${GREEN}✓ MoviePilot-2/ 将被忽略${NC}"
        else
            echo -e "${RED}✗ MoviePilot-2/ 不会被忽略！${NC}"
        fi
    fi

    if [ -d "MoviePilot-Frontend-2" ]; then
        if git check-ignore -q MoviePilot-Frontend-2/; then
            echo -e "${GREEN}✓ MoviePilot-Frontend-2/ 将被忽略${NC}"
        else
            echo -e "${RED}✗ MoviePilot-Frontend-2/ 不会被忽略！${NC}"
        fi
    fi

    if [ -d "MoviePilot-Resources" ]; then
        if git check-ignore -q MoviePilot-Resources/; then
            echo -e "${GREEN}✓ MoviePilot-Resources/ 将被忽略${NC}"
        else
            echo -e "${RED}✗ MoviePilot-Resources/ 不会被忽略！${NC}"
        fi
    fi
else
    echo -e "${RED}✗ .gitignore 文件不存在${NC}"
    exit 1
fi
echo ""

# 7. 查看将要提交的文件
echo -e "${BLUE}7. 查看将要提交的文件...${NC}"
echo "以下文件将被添加到 Git："
echo ""
git status --short | head -20
echo ""
TOTAL_FILES=$(git status --short | wc -l)
echo "总计: $TOTAL_FILES 个文件"
echo ""

# 8. 确认是否继续
read -p "是否继续添加文件并创建首次提交？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

# 9. 添加文件
echo -e "${BLUE}9. 添加文件到 Git...${NC}"
git add .
echo -e "${GREEN}✓ 文件已添加${NC}"
echo ""

# 10. 创建首次提交
echo -e "${BLUE}10. 创建首次提交...${NC}"
git commit -m "Initial commit: WeCom Commander v1.0.0

- 完整的后端实现（FastAPI + Python）
- 现代化前端界面（Vue 3 + TypeScript + Vuetify）
- Docker 容器化部署
- 企业微信集成（消息推送、指令接收、菜单交互）
- 完善的部署文档

基于 MoviePilot 项目精简而来，专注于企业微信功能。"

echo -e "${GREEN}✓ 首次提交已创建${NC}"
echo ""

# 11. 推送到 GitHub
echo -e "${BLUE}11. 推送到 GitHub...${NC}"
read -p "是否立即推送到 GitHub？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git branch -M main

    echo "正在推送..."
    if git push -u origin main; then
        echo -e "${GREEN}✓ 推送成功！${NC}"
        echo ""
        echo "=================================="
        echo "Git 初始化完成！"
        echo "=================================="
        echo ""
        echo "仓库地址: https://github.com/kaiann2021/wecom-cmder"
        echo ""
        echo "后续操作："
        echo "  git add .              # 添加修改"
        echo "  git commit -m 'msg'    # 提交修改"
        echo "  git push               # 推送到 GitHub"
    else
        echo -e "${RED}✗ 推送失败${NC}"
        echo ""
        echo "可能的原因："
        echo "1. 远程仓库不存在或无权限"
        echo "2. SSH 密钥未配置"
        echo "3. 网络连接问题"
        echo ""
        echo "请检查后手动推送："
        echo "  git push -u origin main"
    fi
else
    echo "已跳过推送"
    echo ""
    echo "稍后可以手动推送："
    echo "  git branch -M main"
    echo "  git push -u origin main"
fi

echo ""
echo "=================================="
echo "完成！"
echo "=================================="
