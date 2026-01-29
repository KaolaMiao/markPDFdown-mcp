@echo off
REM 服务器更新脚本 (Windows 版本)
REM 使用方法：update.bat [选项]
REM 选项：
REM   --full     完整更新（重建所有镜像）
REM   --backend  只更新后端
REM   --frontend 只更新前端
REM   --fast     快速更新（不重建，仅重启）

setlocal enabledelayedexpansion

REM 默认选项
set UPDATE_MODE=full

REM 解析参数
:parse_args
if "%~1"=="" goto end_parse
if "%~1"=="--full" (
    set UPDATE_MODE=full
    shift
    goto parse_args
)
if "%~1"=="--backend" (
    set UPDATE_MODE=backend
    shift
    goto parse_args
)
if "%~1"=="--frontend" (
    set UPDATE_MODE=frontend
    shift
    goto parse_args
)
if "%~1"=="--fast" (
    set UPDATE_MODE=fast
    shift
    goto parse_args
)
if "%~1"=="--help" (
    goto show_usage
)
echo [ERROR] 未知选项: %~1
goto show_usage
:end_parse

REM 检查是否在项目目录
if not exist "docker-compose.yml" (
    echo [ERROR] 未找到 docker-compose.yml，请在项目根目录执行此脚本
    exit /b 1
)

echo ========================================
echo   MarkPDFdown-MCP 服务器更新工具
echo ========================================
echo.
echo 更新模式: %UPDATE_MODE%
echo.

REM 1. 检查 Git 状态
echo [INFO] 步骤 1/5: 检查 Git 状态...
if not exist ".git" (
    echo [ERROR] 不是 Git 仓库
    exit /b 1
)

REM 显示当前版本
for /f "delims=" %%i in ('git describe --tags --abbrev=0 2^>nul') do set CURRENT_VERSION=%%i
if not defined CURRENT_VERSION set CURRENT_VERSION=未发布
echo [INFO] 当前版本: %CURRENT_VERSION%
echo.

REM 2. 拉取最新代码
echo [INFO] 步骤 2/5: 拉取最新代码...
git fetch origin
for /f "delims=" %%i in ('git rev-parse HEAD') do set LOCAL=%%i
for /f "delims=" %%i in ('git rev-parse origin/main') do set REMOTE=%%i

if "%LOCAL%"=="%REMOTE%" (
    echo [SUCCESS] 代码已是最新版本
    if not "%UPDATE_MODE%"=="fast" (
        echo [INFO] 如需强制重建，请使用: update.bat --full
        pause
        exit /b 0
    )
) else (
    git pull origin main
    if errorlevel 1 (
        echo [ERROR] 拉取代码失败
        pause
        exit /b 1
    )
    echo [SUCCESS] 代码已更新
)
echo.

REM 3. 备份数据
echo [INFO] 步骤 3/5: 备份重要数据...
set BACKUP_DIR=backup_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
mkdir %BACKUP_DIR% 2>nul

if exist "backend\tasks.db" (
    copy backend\tasks.db %BACKUP_DIR%\ >nul
    echo [INFO] 已备份数据库到: %BACKUP_DIR%\tasks.db
)

if exist "backend\.env" (
    copy backend\.env %BACKUP_DIR%\ >nul
    echo [INFO] 已备份配置到: %BACKUP_DIR%\.env
)

echo [SUCCESS] 备份完成
echo.

REM 4. 停止服务
echo [INFO] 步骤 4/5: 停止服务...
docker-compose down
if errorlevel 1 (
    echo [WARNING] 停止服务失败（可能服务未运行）
)
echo [SUCCESS] 服务已停止
echo.

REM 5. 根据模式更新
echo [INFO] 步骤 5/5: 更新服务...

if "%UPDATE_MODE%"=="full" (
    echo [INFO] 执行完整更新（重建所有镜像）...
    docker-compose up -d --build
    goto after_update
)

if "%UPDATE_MODE%"=="backend" (
    echo [INFO] 只更新后端服务...
    docker-compose up -d --build backend
    goto after_update
)

if "%UPDATE_MODE%"=="frontend" (
    echo [INFO] 只更新前端服务...
    docker-compose up -d --build frontend
    goto after_update
)

if "%UPDATE_MODE%"=="fast" (
    echo [INFO] 快速重启（不重建镜像）...
    docker-compose up -d
    goto after_update
)

:after_update
if errorlevel 1 (
    echo [ERROR] 启动服务失败
    pause
    exit /b 1
)

echo [SUCCESS] 服务已启动
echo.

REM 等待服务启动
echo [INFO] 等待服务启动...
timeout /t 5 /nobreak >nul

REM 检查服务状态
echo [INFO] 检查服务状态...
docker-compose ps
echo.

REM 检查后端健康
echo [INFO] 检查后端健康...
curl -f http://localhost:18000/health >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 后端服务异常 ✗
    echo [INFO] 查看日志: docker-compose logs backend
    pause
    exit /b 1
) else (
    echo [SUCCESS] 后端服务正常 ✓
)

echo.
echo ========================================
echo   更新完成！
echo ========================================
echo.
echo 查看日志:
echo   docker-compose logs -f backend
echo   docker-compose logs -f frontend
echo.
echo 查看服务状态:
echo   docker-compose ps
echo.
echo 如有问题，回滚备份:
echo   copy %BACKUP_DIR%\tasks.db backend\tasks.db
echo   docker-compose restart
echo.
pause
goto end

:show_usage
echo 用法: %~nx0 [选项]
echo.
echo 选项:
echo   --full     完整更新（重建所有镜像）- 推荐
echo   --backend  只更新后端服务
echo   --frontend 只更新前端服务
echo   --fast     快速更新（不重建，仅重启）
echo   --help     显示此帮助信息
echo.
echo 示例:
echo   %~nx0 --full       # 完整更新所有服务
echo   %~nx0 --backend    # 只更新后端
echo   %~nx0 --fast       # 快速重启（无代码更新）
echo.
pause
exit /b 0

:end
