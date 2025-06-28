@echo off
chcp 65001
echo ========================================
echo     数据中心爬虫 - 快速启动
echo ========================================
echo.

echo 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

echo Python环境正常
echo.

echo 正在安装依赖包...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 依赖包安装失败，请检查网络连接
    pause
    exit /b 1
)

echo.
echo 依赖包安装完成
echo.

echo ========================================
echo 选择要运行的爬虫版本:
echo 1. 自动版本 (推荐) - 自动管理ChromeDriver
echo 2. 简化版本 - 需要手动配置ChromeDriver  
echo 3. 完整版本 - 功能最全但配置复杂
echo ========================================
echo.

set /p choice="请输入选择 (1-3): "

if "%choice%"=="1" (
    echo 运行自动版本爬虫...
    python auto_datacenter_crawler.py
) else if "%choice%"=="2" (
    echo 运行简化版本爬虫...
    python simple_datacenter_crawler.py
) else if "%choice%"=="3" (
    echo 运行完整版本爬虫...
    python datacenter_crawler.py
) else (
    echo 无效选择，默认运行自动版本...
    python auto_datacenter_crawler.py
)

echo.
echo ========================================
echo 爬取完成！请查看生成的CSV和JSON文件
echo ========================================

pause
