@echo off
chcp 65001 >nul
echo ================================================
echo 广东省数据中心爬虫项目
echo ================================================
echo.

echo [1] 整理项目文件夹
echo [2] 运行广东省数据中心爬虫
echo [3] 查看项目结构
echo [4] 退出
echo.

set /p choice=请选择操作 (1-4): 

if "%choice%"=="1" (
    echo.
    echo 🔧 正在整理项目文件夹...
    python scripts\organize_project.py
    echo.
    pause
    goto :start
)

if "%choice%"=="2" (
    echo.
    echo 🚀 启动广东省数据中心爬虫...
    python src\guangdong_datacenter_crawler.py
    echo.
    pause
    goto :start
)

if "%choice%"=="3" (
    echo.
    echo 📁 项目目录结构:
    tree /f /a
    echo.
    pause
    goto :start
)

if "%choice%"=="4" (
    echo 再见！
    exit /b 0
)

echo 无效选择，请重新输入。
pause
:start
cls
goto :eof
