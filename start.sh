#!/bin/bash

# WeCom Commander 快速启动脚本

echo "================================"
echo "WeCom Commander 快速启动"
echo "================================"
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: 未安装 Docker"
    echo "请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ 错误: 未安装 Docker Compose"
    echo "请先安装 Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker 环境检查通过"
echo ""

# 创建数据目录
echo "📁 创建数据目录..."
mkdir -p data
echo "✅ 数据目录创建完成"
echo ""

# 启动服务
echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo ""
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "🔍 检查服务状态..."
docker-compose ps

# 健康检查
echo ""
echo "🏥 健康检查..."
if curl -f http://localhost:8000/health &> /dev/null; then
    echo "✅ 服务启动成功！"
    echo ""
    echo "================================"
    echo "访问地址："
    echo "  - API 文档: http://localhost:8000/docs"
    echo "  - 健康检查: http://localhost:8000/health"
    echo "  - API 根路径: http://localhost:8000/api/v1"
    echo "================================"
    echo ""
    echo "📝 下一步："
    echo "  1. 访问 API 文档配置企业微信"
    echo "  2. 查看日志: docker-compose logs -f backend"
    echo "  3. 停止服务: docker-compose down"
else
    echo "❌ 服务启动失败，请查看日志："
    echo "   docker-compose logs backend"
fi
