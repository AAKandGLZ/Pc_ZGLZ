#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上海数据中心网站测试爬虫
专门测试 https://www.datacenters.com/locations/china/shanghai
"""

import time
import os
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

class ShanghaiDatacenterTester:
    def __init__(self):
        self.base_url = "https://www.datacenters.com/locations/china/shanghai"
        
        # Chrome设置
        self.chrome_options = Options()
        # 不使用无头模式，便于观察
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = None
        
        # 输出目录
        os.makedirs("data/shanghai", exist_ok=True)
        os.makedirs("html_sources/shanghai", exist_ok=True)
    
    def setup_driver(self):
        """初始化WebDriver"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.implicitly_wait(10)
            print("✅ WebDriver初始化成功")
            return True
        except Exception as e:
            print(f"❌ WebDriver初始化失败: {e}")
            return False
    
    def load_and_analyze_page(self):
        """加载页面并分析结构"""
        print("🌐 加载目标页面...")
        
        try:
            self.driver.get(self.base_url)
            time.sleep(8)  # 等待页面完全加载
            
            print("✅ 页面加载成功")
            
            # 保存页面源码
            with open("html_sources/shanghai/test_page_source.html", 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            print("📄 页面源码已保存")
            
            # 分析页面基本信息
            title = self.driver.title
            print(f"📋 页面标题: {title}")
            
            # 查找分页元素
            self.analyze_pagination()
            
            # 查找数据元素
            self.analyze_data_elements()
            
            # 尝试提取JavaScript数据
            self.extract_javascript_data()
            
        except Exception as e:
            print(f"❌ 页面加载失败: {e}")
            import traceback
            traceback.print_exc()
    
    def analyze_pagination(self):
        """分析分页结构"""
        print("\n🔍 分析分页结构...")
        
        # 查找常见的分页元素
        pagination_selectors = [
            ".pagination", ".pager", ".page-navigation", ".paginate",
            "[class*='pagination']", "[class*='pager']"
        ]
        
        pagination_found = False
        for selector in pagination_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"  找到分页容器: {selector} ({len(elements)}个)")
                    pagination_found = True
                    
                    # 分析分页容器内容
                    for i, elem in enumerate(elements):
                        print(f"    分页容器{i+1}: {elem.get_attribute('outerHTML')[:200]}...")
            except:
                continue
        
        if not pagination_found:
            print("  ⚠️ 未找到明显的分页容器")
        
        # 查找页码按钮
        print("\n🔢 查找页码按钮...")
        button_selectors = [
            "a[onclick*='page']", "button[onclick*='page']", "[data-page]",
            ".page-number", ".page-btn"
        ]
        
        buttons_found = False
        for selector in button_selectors:
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if buttons:
                    print(f"  找到页码按钮: {selector} ({len(buttons)}个)")
                    buttons_found = True
                    
                    for i, btn in enumerate(buttons[:5]):  # 只显示前5个
                        text = btn.text.strip()
                        onclick = btn.get_attribute('onclick')
                        data_page = btn.get_attribute('data-page')
                        print(f"    按钮{i+1}: 文本='{text}', onclick='{onclick}', data-page='{data_page}'")
            except:
                continue
        
        if not buttons_found:
            print("  ⚠️ 未找到明显的页码按钮")
        
        # 手动查找数字按钮
        print("\n🔍 手动查找数字按钮...")
        for i in range(1, 6):
            xpath_selectors = [
                f"//a[text()='{i}']",
                f"//button[text()='{i}']",
                f"//span[text()='{i}']"
            ]
            
            for xpath in xpath_selectors:
                try:
                    elem = self.driver.find_element(By.XPATH, xpath)
                    if elem.is_displayed():
                        print(f"  找到数字按钮 {i}: {xpath}")
                        print(f"    HTML: {elem.get_attribute('outerHTML')}")
                        break
                except:
                    continue
    
    def analyze_data_elements(self):
        """分析数据元素"""
        print("\n📊 分析数据元素...")
        
        # 查找可能包含坐标的元素
        data_selectors = [
            "[data-lat]", "[data-latitude]", "[data-lng]", "[data-longitude]",
            ".marker", ".location", ".datacenter", ".facility"
        ]
        
        data_found = False
        for selector in data_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"  找到数据元素: {selector} ({len(elements)}个)")
                    data_found = True
                    
                    # 显示前几个元素的详情
                    for i, elem in enumerate(elements[:3]):
                        lat = elem.get_attribute('data-lat') or elem.get_attribute('data-latitude')
                        lng = elem.get_attribute('data-lng') or elem.get_attribute('data-longitude')
                        title = elem.get_attribute('title')
                        text = elem.text.strip()[:100]
                        
                        print(f"    元素{i+1}: lat={lat}, lng={lng}, title='{title}', text='{text}'")
            except:
                continue
        
        if not data_found:
            print("  ⚠️ 未找到明显的数据元素")
    
    def extract_javascript_data(self):
        """提取JavaScript数据"""
        print("\n💻 提取JavaScript数据...")
        
        js_variables = [
            "window.datacenters", "window.locations", "window.facilities",
            "window.markers", "window.mapData", "window.sites"
        ]
        
        data_found = False
        for var in js_variables:
            try:
                result = self.driver.execute_script(f"return {var};")
                if result:
                    print(f"  找到JS变量: {var}")
                    print(f"    类型: {type(result)}")
                    if isinstance(result, (list, dict)):
                        print(f"    长度/键数: {len(result)}")
                        
                        # 如果是列表且包含坐标数据，显示样例
                        if isinstance(result, list) and result:
                            sample = result[0]
                            if isinstance(sample, dict):
                                print(f"    样例数据: {sample}")
                                
                                # 统计包含坐标的项目
                                coord_count = 0
                                for item in result:
                                    if isinstance(item, dict):
                                        has_lat = 'latitude' in item or 'lat' in item
                                        has_lng = 'longitude' in item or 'lng' in item
                                        if has_lat and has_lng:
                                            coord_count += 1
                                
                                print(f"    包含坐标的项目: {coord_count}/{len(result)}")
                    
                    data_found = True
                    
                    # 保存数据
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    var_name = var.replace('window.', '')
                    json_file = f"data/shanghai/js_data_{var_name}_{timestamp}.json"
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    print(f"    数据已保存: {json_file}")
                    
            except Exception as e:
                print(f"  {var}: 无数据或出错 ({e})")
        
        if not data_found:
            print("  ⚠️ 未找到JavaScript数据变量")
    
    def test_button_click(self):
        """测试页码按钮点击"""
        print("\n🖱️ 测试页码按钮点击...")
        
        # 尝试找到第2页按钮
        button_selectors = [
            "//a[text()='2']",
            "//button[text()='2']",
            "//span[text()='2']",
            "//a[@data-page='2']",
            "//button[@data-page='2']"
        ]
        
        for selector in button_selectors:
            try:
                button = self.driver.find_element(By.XPATH, selector)
                if button.is_displayed():
                    print(f"  找到第2页按钮: {selector}")
                    print(f"    按钮HTML: {button.get_attribute('outerHTML')}")
                    
                    # 尝试点击
                    try:
                        print("  🖱️ 尝试点击第2页按钮...")
                        button.click()
                        time.sleep(5)  # 等待页面响应
                        
                        print("  ✅ 点击成功，检查页面变化...")
                        
                        # 重新提取JavaScript数据看是否有变化
                        self.extract_javascript_data()
                        
                        return True
                        
                    except Exception as click_error:
                        print(f"  ❌ 点击失败: {click_error}")
                        
            except:
                continue
        
        print("  ❌ 未找到可点击的第2页按钮")
        return False
    
    def run_test(self):
        """运行完整测试"""
        print("🚀 开始上海数据中心网站测试")
        print("🎯 目标网址: https://www.datacenters.com/locations/china/shanghai")
        print("="*70)
        
        if not self.setup_driver():
            return
        
        try:
            # 1. 加载和分析页面
            self.load_and_analyze_page()
            
            # 2. 测试按钮点击
            self.test_button_click()
            
            print(f"\n{'='*70}")
            print("📊 测试完成！")
            print("💡 请检查输出目录中的保存文件:")
            print("   - html_sources/shanghai/test_page_source.html")
            print("   - data/shanghai/js_data_*.json")
            
        except Exception as e:
            print(f"❌ 测试过程出错: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n⏸️ 浏览器将在10秒后关闭...")
            time.sleep(10)
            if self.driver:
                self.driver.quit()

def main():
    """主函数"""
    print("🧪 上海数据中心网站结构测试")
    print("🔍 分析页面结构、分页机制和数据提取")
    
    tester = ShanghaiDatacenterTester()
    tester.run_test()

if __name__ == "__main__":
    main()
