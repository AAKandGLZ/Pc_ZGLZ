@echo off
echo 数据中心爬虫安装脚本
echo =====================

echo.
echo 正在安装Python依赖包...
pip install -r requirements.txt

echo.
echo 正在检查Chrome浏览器...
where chrome >nul 2>nul
if %errorlevel% neq 0 (
    echo 警告: 未找到Chrome浏览器，请确保已安装Chrome
) else (
    echo Chrome浏览器已找到
)

echo.
echo 正在下载ChromeDriver...
echo 请手动下载ChromeDriver并放置在系统PATH中
echo 下载地址: https://chromedriver.chromium.org/
echo 或者使用webdriver-manager自动管理:
pip install webdriver-manager

echo.
echo 安装完成！
echo 使用方法:
echo   python simple_datacenter_crawler.py
echo   或
echo   python datacenter_crawler.py

pause
