#!/bin/bash

# WeCom Commander 部署前检查脚本

set -e

echo "=================================="
echo "WeCom Commander 部署前检查"
echo "=================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 已安装"
        return 0
    else
        echo -e "${RED}✗${NC} $1 未安装"
        return 1
    fi
}

check_port() {
    if netstat -tuln 2>/dev/null | grep -q ":$1 "; then
        echo -e "${YELLOW}⚠${NC} 端口 $1 已被占用"
        return 1
    else
        echo -e "${GREEN}✓${NC} 端口 $1 可用"
        return 0
    fi
}

# 1. 检查系统要求
echo "1. 检查系统要求"
echo "-------------------"

# 检查操作系统
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo -e "${GREEN}✓${NC} 操作系统: $NAME $VERSION"
else
    echo -e "${YELLOW}⚠${NC} 无法检测操作系统"
fi

# 检查 CPU 核心数
CPU_CORES=$(nproc)
if [ $CPU_CORES -ge 2 ]; then
    echo -e "${GREEN}✓${NC} CPU 核心数: $CPU_CORES"
else
    echo -e "${YELLOW}⚠${NC} CPU 核心数: $CPU_CORES (建议至少2核)"
fi

# 检查内存
TOTAL_MEM=$(free -m | awk 'NR==2{print $2}')
if [ $TOTAL_MEM -ge 2000 ]; then
    echo -e "${GREEN}✓${NC} 内存: ${TOTAL_MEM}MB"
else
    echo -e "${YELLOW}⚠${NC} 内存: ${TOTAL_MEM}MB (建议至少2GB)"
fi

# 检查磁盘空间
DISK_SPACE=$(df -BG . | awk 'NR==2{print $4}' | sed 's/G//')
if [ $DISK_SPACE -ge 10 ]; then
    echo -e "${GREEN}✓${NC} 可用磁盘空间: ${DISK_SPACE}GB"
else
    echo -e "${YELLOW}⚠${NC} 可用磁盘空间: ${DISK_SPACE}GB (建议至少10GB)"
fi

echo ""

# 2. 检查必要软件
echo "2. 检查必要软件"
echo "-------------------"

DOCKER_OK=0
COMPOSE_OK=0

if check_command docker; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    echo "   版本: $DOCKER_VERSION"
    DOCKER_OK=1
fi

if check_command "docker compose" || check_command "docker-compose"; then
    if docker compose version &> /dev/null; then
        COMPOSE_VERSION=$(docker compose version | awk '{print $4}')
    else
        COMPOSE_VERSION=$(docker-compose --version | awk '{print $4}' | sed 's/,//')
    fi
    echo "   版本: $COMPOSE_VERSION"
    COMPOSE_OK=1
fi

check_command git

echo ""

# 3. 检查 Docker 服务
echo "3. 检查 Docker 服务"
echo "-------------------"

if systemctl is-active --quiet docker; then
    echo -e "${GREEN}✓${NC} Docker 服务运行中"
else
    echo -e "${RED}✗${NC} Docker 服务未运行"
    echo "   请执行: sudo systemctl start docker"
fi

# 检查 Docker 权限
if docker ps &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker 权限正常"
else
    echo -e "${YELLOW}⚠${NC} 需要 sudo 权限运行 Docker"
    echo "   建议执行: sudo usermod -aG docker \$USER"
fi

echo ""

# 4. 检查端口占用
echo "4. 检查端口占用"
echo "-------------------"

check_port 80
check_port 443
check_port 3000
check_port 8000

echo ""

# 5. 检查项目文件
echo "5. 检查项目文件"
echo "-------------------"

REQUIRED_FILES=(
    "docker-compose.yml"
    "backend/Dockerfile"
    "backend/requirements.txt"
    "backend/app/main.py"
    "frontend/Dockerfile"
    "frontend/package.json"
    "README.md"
)

ALL_FILES_OK=1
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file 不存在"
        ALL_FILES_OK=0
    fi
done

echo ""

# 6. 检查配置文件
echo "6. 检查配置文件"
echo "-------------------"

if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env 文件存在"

    # 检查关键配置
    if grep -q "CORS_ORIGINS" .env; then
        echo -e "${GREEN}✓${NC} CORS_ORIGINS 已配置"
    else
        echo -e "${YELLOW}⚠${NC} CORS_ORIGINS 未配置"
    fi
else
    echo -e "${YELLOW}⚠${NC} .env 文件不存在（将使用默认配置）"
fi

echo ""

# 7. 检查网络连接
echo "7. 检查网络连接"
echo "-------------------"

if ping -c 1 8.8.8.8 &> /dev/null; then
    echo -e "${GREEN}✓${NC} 网络连接正常"
else
    echo -e "${RED}✗${NC} 网络连接失败"
fi

if curl -s https://registry.hub.docker.com &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker Hub 可访问"
else
    echo -e "${YELLOW}⚠${NC} Docker Hub 访问失败（可能需要配置镜像加速）"
fi

echo ""

# 8. 生成部署建议
echo "=================================="
echo "部署建议"
echo "=================================="
echo ""

if [ $DOCKER_OK -eq 0 ]; then
    echo -e "${RED}✗ 必须安装 Docker${NC}"
    echo "   Ubuntu/Debian: sudo apt-get install docker-ce docker-ce-cli containerd.io"
    echo "   CentOS/RHEL: sudo yum install docker-ce docker-ce-cli containerd.io"
    echo ""
fi

if [ $COMPOSE_OK -eq 0 ]; then
    echo -e "${RED}✗ 必须安装 Docker Compose${NC}"
    echo "   sudo apt-get install docker-compose-plugin"
    echo ""
fi

if [ $ALL_FILES_OK -eq 0 ]; then
    echo -e "${RED}✗ 项目文件不完整${NC}"
    echo "   请确保所有必要文件都已上传"
    echo ""
fi

# 生成部署命令
echo "如果所有检查通过，可以执行以下命令部署："
echo ""
echo -e "${GREEN}# 创建必要目录${NC}"
echo "mkdir -p data logs"
echo ""
echo -e "${GREEN}# 构建镜像${NC}"
echo "docker compose build"
echo ""
echo -e "${GREEN}# 启动服务${NC}"
echo "docker compose up -d"
echo ""
echo -e "${GREEN}# 查看状态${NC}"
echo "docker compose ps"
echo ""
echo -e "${GREEN}# 查看日志${NC}"
echo "docker compose logs -f"
echo ""

# 生成 Nginx 配置建议
echo "=================================="
echo "Nginx 配置建议"
echo "=================================="
echo ""
echo "如果需要配置 Nginx 反向代理，请参考 DEPLOYMENT.md"
echo ""

# 总结
echo "=================================="
echo "检查完成"
echo "=================================="
echo ""

if [ $DOCKER_OK -eq 1 ] && [ $COMPOSE_OK -eq 1 ] && [ $ALL_FILES_OK -eq 1 ]; then
    echo -e "${GREEN}✓ 系统已准备就绪，可以开始部署${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ 请先解决上述问题后再部署${NC}"
    exit 1
fi
