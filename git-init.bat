@echo off
REM WeCom Commander Git 初始化脚本 (Windows)

setlocal enabledelayedexpansion

echo ==================================
echo WeCom Commander Git 初始化
echo ==================================
echo.

REM 仓库信息
set REPO_URL=prv:kaiann2021/wecom-cmder.git
set REPO_HTTPS=https://github.com/kaiann2021/wecom-cmder.git

REM 1. 检查 Git 是否安装
echo 1. 检查 Git 安装...
git --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Git 未安装
    echo 请先安装 Git: https://git-scm.com/downloads
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('git --version') do set GIT_VERSION=%%i
echo [成功] Git 已安装: !GIT_VERSION!
echo.

REM 2. 检查是否已经是 Git 仓库
echo 2. 检查 Git 仓库状态...
if exist ".git" (
    echo [警告] 已经是 Git 仓库
    echo 如需重新初始化，请先删除 .git 目录
    set /p CONTINUE="是否继续？(y/n) "
    if /i not "!CONTINUE!"=="y" exit /b 0
) else (
    echo [成功] 未初始化 Git 仓库
)
echo.

REM 3. 检查 SSH 配置
echo 3. 检查 SSH 配置...
ssh -T prv 2>&1 | findstr /C:"successfully authenticated" >nul
if errorlevel 1 (
    echo [警告] SSH 配置未找到或未配置
    echo 将使用 HTTPS 方式
    set USE_SSH=false
) else (
    echo [成功] SSH 配置正确（使用 prv Host）
    set USE_SSH=true
)
echo.

REM 4. 初始化 Git 仓库
echo 4. 初始化 Git 仓库...
if not exist ".git" (
    git init
    echo [成功] Git 仓库初始化完成
) else (
    echo [警告] Git 仓库已存在
)
echo.

REM 5. 配置远程仓库
echo 5. 配置远程仓库...
git remote | findstr "origin" >nul
if not errorlevel 1 (
    echo [警告] 远程仓库 origin 已存在
    git remote -v
    set /p UPDATE="是否更新远程仓库地址？(y/n) "
    if /i "!UPDATE!"=="y" (
        git remote remove origin
        if "!USE_SSH!"=="true" (
            git remote add origin !REPO_URL!
        ) else (
            git remote add origin !REPO_HTTPS!
        )
        echo [成功] 远程仓库已更新
    )
) else (
    if "!USE_SSH!"=="true" (
        git remote add origin !REPO_URL!
        echo [成功] 远程仓库已添加（SSH）
    ) else (
        git remote add origin !REPO_HTTPS!
        echo [成功] 远程仓库已添加（HTTPS）
    )
)
git remote -v
echo.

REM 6. 检查 .gitignore 配置
echo 6. 检查 .gitignore 配置...
if exist ".gitignore" (
    echo [成功] .gitignore 文件存在

    REM 检查 MoviePilot 目录是否会被忽略
    if exist "MoviePilot-2" (
        git check-ignore -q MoviePilot-2/ >nul 2>&1
        if not errorlevel 1 (
            echo [成功] MoviePilot-2/ 将被忽略
        ) else (
            echo [错误] MoviePilot-2/ 不会被忽略！
        )
    )

    if exist "MoviePilot-Frontend-2" (
        git check-ignore -q MoviePilot-Frontend-2/ >nul 2>&1
        if not errorlevel 1 (
            echo [成功] MoviePilot-Frontend-2/ 将被忽略
        ) else (
            echo [错误] MoviePilot-Frontend-2/ 不会被忽略！
        )
    )

    if exist "MoviePilot-Resources" (
        git check-ignore -q MoviePilot-Resources/ >nul 2>&1
        if not errorlevel 1 (
            echo [成功] MoviePilot-Resources/ 将被忽略
        ) else (
            echo [错误] MoviePilot-Resources/ 不会被忽略！
        )
    )
) else (
    echo [错误] .gitignore 文件不存在
    pause
    exit /b 1
)
echo.

REM 7. 查看将要提交的文件
echo 7. 查看将要提交的文件...
echo 以下文件将被添加到 Git：
echo.
git status --short | more
echo.

REM 8. 确认是否继续
set /p CONTINUE="是否继续添加文件并创建首次提交？(y/n) "
if /i not "!CONTINUE!"=="y" (
    echo 已取消
    pause
    exit /b 0
)

REM 9. 添加文件
echo.
echo 9. 添加文件到 Git...
git add .
echo [成功] 文件已添加
echo.

REM 10. 创建首次提交
echo 10. 创建首次提交...
git commit -m "Initial commit: WeCom Commander v1.0.0" -m "- 完整的后端实现（FastAPI + Python）" -m "- 现代化前端界面（Vue 3 + TypeScript + Vuetify）" -m "- Docker 容器化部署" -m "- 企业微信集成（消息推送、指令接收、菜单交互）" -m "- 完善的部署文档" -m "" -m "基于 MoviePilot 项目精简而来，专注于企业微信功能。"
echo [成功] 首次提交已创建
echo.

REM 11. 推送到 GitHub
echo 11. 推送到 GitHub...
set /p PUSH="是否立即推送到 GitHub？(y/n) "
if /i "!PUSH!"=="y" (
    git branch -M main
    echo 正在推送...
    git push -u origin main
    if errorlevel 1 (
        echo [错误] 推送失败
        echo.
        echo 可能的原因：
        echo 1. 远程仓库不存在或无权限
        echo 2. SSH 密钥未配置
        echo 3. 网络连接问题
        echo.
        echo 请检查后手动推送：
        echo   git push -u origin main
    ) else (
        echo [成功] 推送成功！
        echo.
        echo ==================================
        echo Git 初始化完成！
        echo ==================================
        echo.
        echo 仓库地址: https://github.com/kaiann2021/wecom-cmder
        echo.
        echo 后续操作：
        echo   git add .              # 添加修改
        echo   git commit -m "msg"    # 提交修改
        echo   git push               # 推送到 GitHub
    )
) else (
    echo 已跳过推送
    echo.
    echo 稍后可以手动推送：
    echo   git branch -M main
    echo   git push -u origin main
)

echo.
echo ==================================
echo 完成！
echo ==================================
pause
