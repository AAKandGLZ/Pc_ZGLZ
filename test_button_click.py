#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
页码按钮点击测试爬虫
使用本地HTML文件测试Selenium的页码按钮点击功能
"""

import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

class ButtonClickTester:
    def __init__(self):
        # 设置Chrome选项
        self.chrome_options = Options()
        # 不使用无头模式，便于观察
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1200,800')
        
        self.driver = None
        
        # 本地测试文件路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_file = f"file:///{current_dir}/test_pagination.html".replace('\\', '/')
    
    def setup_driver(self):
        """初始化WebDriver"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.implicitly_wait(5)
            print("✅ WebDriver初始化成功")
            return True
        except Exception as e:
            print(f"❌ WebDriver初始化失败: {e}")
            return False
    
    def load_test_page(self):
        """加载测试页面"""
        print(f"🌐 加载测试页面: {self.test_file}")
        try:
            self.driver.get(self.test_file)
            time.sleep(2)
            print("✅ 测试页面加载成功")
            return True
        except Exception as e:
            print(f"❌ 测试页面加载失败: {e}")
            return False
    
    def find_page_buttons(self):
        """查找页码按钮"""
        print("🔍 查找页码按钮...")
        
        page_buttons = {}
        
        # 查找具有onclick属性的按钮
        try:
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "a[onclick*='goToPage']")
            for btn in buttons:
                onclick = btn.get_attribute('onclick')
                text = btn.text.strip()
                
                if text.isdigit():
                    page_num = int(text)
                    page_buttons[page_num] = btn
                    print(f"  找到页码按钮 {page_num}: {onclick}")
        except Exception as e:
            print(f"  查找onclick按钮失败: {e}")
        
        # 查找ID为page-X的按钮
        for i in range(1, 6):
            try:
                btn = self.driver.find_element(By.ID, f"page-{i}")
                if btn.is_displayed():
                    page_buttons[i] = btn
                    print(f"  找到页码按钮 {i}: ID=page-{i}")
            except:
                continue
        
        print(f"🔢 总共找到 {len(page_buttons)} 个页码按钮: {list(page_buttons.keys())}")
        return page_buttons
    
    def click_page_button(self, page_number, page_buttons):
        """点击指定页码按钮"""
        print(f"🖱️ 点击第 {page_number} 页按钮...")
        
        if page_number not in page_buttons:
            print(f"  ❌ 未找到第 {page_number} 页按钮")
            return False
        
        button = page_buttons[page_number]
        
        try:
            # 滚动到按钮位置
            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
            time.sleep(0.5)
            
            # 点击按钮
            button.click()
            print(f"  ✅ 成功点击第 {page_number} 页按钮")
            time.sleep(2)  # 等待页面更新
            return True
            
        except Exception as e:
            print(f"  普通点击失败，尝试JavaScript点击: {e}")
            try:
                self.driver.execute_script("arguments[0].click();", button)
                print(f"  ✅ JavaScript点击成功")
                time.sleep(2)
                return True
            except Exception as js_error:
                print(f"  ❌ JavaScript点击也失败: {js_error}")
                return False
    
    def extract_page_data(self, page_num):
        """提取当前页面的数据"""
        print(f"  📄 提取第 {page_num} 页数据...")
        
        datacenters = []
        
        try:
            # 检查当前页面显示
            current_page_elem = self.driver.find_element(By.ID, "current-page")
            displayed_page = current_page_elem.text.strip()
            print(f"    页面显示当前页: {displayed_page}")
            
            # 从JavaScript变量获取数据
            js_data = self.driver.execute_script("return window.datacenters || [];")
            if js_data:
                for item in js_data:
                    if 'lat' in item and 'lng' in item:
                        datacenters.append({
                            'name': item.get('name', f'数据中心_{len(datacenters)+1}'),
                            'latitude': float(item['lat']),
                            'longitude': float(item['lng']),
                            'source_page': page_num,
                            'extraction_method': 'JavaScript'
                        })
                print(f"    从JavaScript获取到 {len(datacenters)} 个数据中心")
            
            # 从DOM元素获取数据
            dom_items = self.driver.find_elements(By.CSS_SELECTOR, ".datacenter-item[data-lat][data-lng]")
            for item in dom_items:
                try:
                    lat = float(item.get_attribute('data-lat'))
                    lng = float(item.get_attribute('data-lng'))
                    name = item.find_element(By.TAG_NAME, 'h3').text.strip()
                    
                    # 避免重复
                    if not any(dc['name'] == name for dc in datacenters):
                        datacenters.append({
                            'name': name,
                            'latitude': lat,
                            'longitude': lng,
                            'source_page': page_num,
                            'extraction_method': 'DOM'
                        })
                except Exception as e:
                    print(f"    DOM提取项目失败: {e}")
            
            print(f"    第 {page_num} 页总共获取到 {len(datacenters)} 个数据中心")
            
        except Exception as e:
            print(f"    第 {page_num} 页数据提取失败: {e}")
        
        return datacenters
    
    def run_test(self):
        """运行测试"""
        print("🚀 开始页码按钮点击测试")
        print("🎯 目标：验证能否正确点击页码按钮并提取数据")
        print("="*60)
        
        if not self.setup_driver():
            return False
        
        try:
            # 1. 加载测试页面
            if not self.load_test_page():
                return False
            
            # 2. 查找页码按钮
            page_buttons = self.find_page_buttons()
            if not page_buttons:
                print("❌ 未找到任何页码按钮")
                return False
            
            # 3. 逐页测试
            total_datacenters = []
            total_pages = max(page_buttons.keys())
            
            for page_num in range(1, total_pages + 1):
                print(f"\n📄 测试第 {page_num} 页 ({page_num}/{total_pages})")
                
                # 如果不是第一页，需要点击页码按钮
                if page_num > 1:
                    success = self.click_page_button(page_num, page_buttons)
                    if not success:
                        print(f"    无法点击第 {page_num} 页按钮，跳过")
                        continue
                
                # 提取页面数据
                page_data = self.extract_page_data(page_num)
                if page_data:
                    total_datacenters.extend(page_data)
                    print(f"    ✅ 第 {page_num} 页获取 {len(page_data)} 个数据中心")
                    
                    # 显示数据详情
                    for i, dc in enumerate(page_data, 1):
                        print(f"      {i}. {dc['name']} ({dc['latitude']}, {dc['longitude']})")
                else:
                    print(f"    ❌ 第 {page_num} 页未获取到数据")
                
                time.sleep(1)  # 页面间延迟
            
            # 4. 测试总结
            print(f"\n{'='*60}")
            print(f"📊 测试完成统计:")
            print(f"  总页数: {total_pages}")
            print(f"  总数据中心: {len(total_datacenters)} 个")
            
            by_page = {}
            for dc in total_datacenters:
                page = dc['source_page']
                by_page[page] = by_page.get(page, 0) + 1
            
            for page_num in sorted(by_page.keys()):
                print(f"  第 {page_num} 页: {by_page[page_num]} 个数据中心")
            
            print(f"\n🎉 页码按钮点击测试{'成功' if len(total_datacenters) > 0 else '失败'}！")
            return len(total_datacenters) > 0
            
        except Exception as e:
            print(f"❌ 测试过程出错: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            print("\n⏸️ 浏览器将在5秒后关闭...")
            time.sleep(5)
            if self.driver:
                self.driver.quit()

def main():
    """主函数"""
    print("🧪 Selenium页码按钮点击功能测试")
    print("📝 验证能否正确识别、点击页码按钮并提取数据")
    
    tester = ButtonClickTester()
    
    try:
        success = tester.run_test()
        
        if success:
            print("\n✅ 测试通过！页码按钮点击功能正常")
            print("💡 可以将此技术应用到真实网站的翻页爬取")
        else:
            print("\n❌ 测试失败！需要检查页码按钮识别或点击逻辑")
            
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断测试")
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")

if __name__ == "__main__":
    main()
