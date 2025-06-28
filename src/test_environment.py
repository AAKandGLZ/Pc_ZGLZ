#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据中心爬虫测试脚本
用于验证爬虫的基本功能
"""

import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def test_basic_connection():
    """测试基本网络连接"""
    print("测试1: 网络连接...")
    try:
        response = requests.get("https://www.datacenters.com", timeout=10)
        if response.status_code == 200:
            print("✓ 网络连接正常")
            return True
        else:
            print(f"✗ 网络连接异常，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 网络连接失败: {e}")
        return False

def test_chrome_driver():
    """测试ChromeDriver设置"""
    print("\n测试2: ChromeDriver配置...")
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 简单测试
        driver.get("https://www.google.com")
        title = driver.title
        driver.quit()
        
        print("✓ ChromeDriver配置成功")
        print(f"  测试页面标题: {title}")
        return True
        
    except Exception as e:
        print(f"✗ ChromeDriver配置失败: {e}")
        return False

def test_target_page():
    """测试目标页面访问"""
    print("\n测试3: 目标页面访问...")
    
    test_url = "https://www.datacenters.com/locations/china/sichuan-sheng"
    
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print(f"  访问: {test_url}")
        driver.get(test_url)
        
        # 等待页面加载
        time.sleep(5)
        
        # 检查页面基本信息
        title = driver.title
        print(f"  页面标题: {title}")
        
        # 查找可能的地图元素
        from selenium.webdriver.common.by import By
        
        selectors_to_test = [
            "gmp-advanced-marker",
            "[position]",
            ".map",
            "script"
        ]
        
        for selector in selectors_to_test:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"  找到 {len(elements)} 个 '{selector}' 元素")
        
        driver.quit()
        print("✓ 目标页面访问成功")
        return True
        
    except Exception as e:
        print(f"✗ 目标页面访问失败: {e}")
        return False

def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("数据中心爬虫 - 环境测试")
    print("=" * 60)
    
    tests = [
        test_basic_connection,
        test_chrome_driver, 
        test_target_page
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ 测试异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"测试完成: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有测试通过，爬虫环境配置正常")
        print("可以运行完整的爬虫脚本了")
    else:
        print("✗ 部分测试失败，请检查环境配置")
        print("建议:")
        print("1. 确保网络连接正常")
        print("2. 确保Chrome浏览器已安装")
        print("3. 检查防火墙设置")
    
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
