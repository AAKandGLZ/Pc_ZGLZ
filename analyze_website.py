#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试目标网站的HTML结构
"""

import requests
from bs4 import BeautifulSoup
import re
import json

def test_direct_request():
    """直接请求页面内容"""
    url = "https://www.datacenters.com/locations/china/sichuan-sheng"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        print(f"请求URL: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"页面内容长度: {len(response.text)} 字符")
            
            # 查找可能包含坐标的内容
            coordinate_patterns = [
                r'"position":"([\d\.,\-]+)"',
                r'position="([\d\.,\-]+)"',
                r'"lat":\s*([\d\.\-]+)',
                r'"lng":\s*([\d\.\-]+)',
                r'"latitude":\s*([\d\.\-]+)',
                r'"longitude":\s*([\d\.\-]+)',
                r'(\d+\.\d+),(\d+\.\d+)'
            ]
            
            found_coordinates = []
            
            for pattern in coordinate_patterns:
                matches = re.findall(pattern, response.text)
                if matches:
                    print(f"模式 '{pattern}' 找到 {len(matches)} 个匹配")
                    found_coordinates.extend(matches)
            
            # 查找可能的地图数据
            map_keywords = [
                "gmp-advanced-marker",
                "google.maps",
                "marker",
                "position",
                "coordinates",
                "datacenter"
            ]
            
            for keyword in map_keywords:
                count = response.text.lower().count(keyword.lower())
                if count > 0:
                    print(f"关键词 '{keyword}' 出现 {count} 次")
            
            # 保存HTML内容用于分析
            with open("e:\\空间统计分析\\爬虫\\page_source.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("页面源码已保存到 page_source.html")
            
            return True
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"请求异常: {e}")
        return False

def test_selenium_simple():
    """简单的Selenium测试"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.common.by import By
        import time
        
        print("\n使用Selenium测试...")
        
        chrome_options = Options()
        # 不使用无头模式，便于观察
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        url = "https://www.datacenters.com/locations/china/sichuan-sheng"
        print(f"访问: {url}")
        
        driver.get(url)
        print("页面加载中...")
        time.sleep(10)
        
        # 获取页面源码
        page_source = driver.page_source
        
        # 查找所有可能的元素
        selectors = [
            "[position]",
            "gmp-advanced-marker", 
            "[class*='marker']",
            "[data-lat]",
            "[data-lng]",
            "script"
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"选择器 '{selector}' 找到 {len(elements)} 个元素")
                    
                    for i, elem in enumerate(elements[:3]):  # 只显示前3个
                        try:
                            if selector == "script":
                                content = elem.get_attribute("innerHTML")
                                if content and ("position" in content or "lat" in content):
                                    print(f"  脚本 {i+1} 包含位置数据")
                            else:
                                attrs = driver.execute_script(
                                    "var items = {}; for (var i = 0, attrs = arguments[0].attributes, l = attrs.length; i < l; i++){ items[attrs.item(i).name] = attrs.item(i).value; } return items;", 
                                    elem
                                )
                                print(f"  元素 {i+1} 属性: {attrs}")
                        except Exception as e:
                            print(f"  获取元素 {i+1} 信息失败: {e}")
            except Exception as e:
                print(f"选择器 '{selector}' 执行失败: {e}")
        
        # 执行JavaScript查找地图数据
        try:
            js_script = """
            var results = [];
            
            // 查找所有带position属性的元素
            var posElements = document.querySelectorAll('[position]');
            posElements.forEach(function(elem, index) {
                results.push({
                    type: 'position_attr',
                    index: index,
                    position: elem.getAttribute('position'),
                    tagName: elem.tagName,
                    className: elem.className
                });
            });
            
            // 查找可能的地图相关变量
            if (window.google && window.google.maps) {
                results.push({type: 'google_maps', found: true});
            }
            
            return results;
            """
            
            js_results = driver.execute_script(js_script)
            if js_results:
                print(f"JavaScript找到 {len(js_results)} 个结果:")
                for result in js_results:
                    print(f"  {result}")
        
        except Exception as e:
            print(f"JavaScript执行失败: {e}")
        
        # 保存截图
        try:
            driver.save_screenshot("e:\\空间统计分析\\爬虫\\page_screenshot.png")
            print("页面截图已保存")
        except:
            pass
        
        driver.quit()
        return True
        
    except Exception as e:
        print(f"Selenium测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("数据中心网站结构分析")
    print("=" * 60)
    
    # 测试1: 直接HTTP请求
    print("测试1: 直接HTTP请求")
    print("-" * 30)
    test_direct_request()
    
    print("\n" + "=" * 60)
    
    # 测试2: Selenium测试
    print("测试2: Selenium分析")
    print("-" * 30)
    test_selenium_simple()
    
    print("\n" + "=" * 60)
    print("分析完成，请查看生成的文件:")
    print("- page_source.html (页面源码)")
    print("- page_screenshot.png (页面截图)")

if __name__ == "__main__":
    main()
