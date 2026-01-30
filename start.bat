@echo off
REM WeCom Commander 快速启动脚本 (Windows)

echo ================================
echo WeCom Commander 快速启动
echo ================================
echo.

REM 检查 Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未安装 Docker
    echo 请先安装 Docker Desktop: https://docs.docker.com/desktop/install/windows-install/
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未安装 Docker Compose
    pause
    exit /b 1
)

echo ✅ Docker 环境检查通过
echo.

REM 创建数据目录
echo 📁 创建数据目录...
if not exist data mkdir data
echo ✅ 数据目录创建完成
echo.

REM 启动服务
echo 🚀 启动服务...
docker-compose up -d

REM 等待服务启动
echo.
echo ⏳ 等待服务启动...
timeout /t 5 /nobreak >nul

REM 检查服务状态
echo.
echo 🔍 检查服务状态...
docker-compose ps

REM 健康检查
echo.
echo 🏥 健康检查...
curl -f http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ❌ 服务启动失败，请查看日志：
    echo    docker-compose logs backend
) else (
    echo ✅ 服务启动成功！
    echo.
    echo ================================
    echo 访问地址：
    echo   - API 文档: http://localhost:8000/docs
    echo   - 健康检查: http://localhost:8000/health
    echo   - API 根路径: http://localhost:8000/api/v1
    echo ================================
    echo.
    echo 📝 下一步：
    echo   1. 访问 API 文档配置企业微信
    echo   2. 查看日志: docker-compose logs -f backend
    echo   3. 停止服务: docker-compose down
)

echo.
pause
