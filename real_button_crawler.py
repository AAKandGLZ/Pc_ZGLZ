#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实页码按钮点击爬虫
专门处理通过Selenium真实点击页面上的页码按钮进行翻页
目标：获取上海数据中心所有页面数据（预期54个）
"""

import requests
import json
import time
import os
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

class RealButtonCrawler:
    def __init__(self):
        self.base_url = "https://www.datacenters.com/locations/china/shanghai"
        
        # 设置Chrome选项
        self.chrome_options = Options()
        # 注释掉无头模式，方便调试
        # self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 添加SSL和网络相关配置
        self.chrome_options.add_argument('--ignore-certificate-errors')
        self.chrome_options.add_argument('--ignore-ssl-errors')
        self.chrome_options.add_argument('--allow-running-insecure-content')
        self.chrome_options.add_argument('--disable-web-security')
        self.chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        
        self.driver = None
        self.all_datacenters = []
        self.page_data = {}
        
        # 创建输出目录
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
    
    def load_initial_page(self):
        """加载初始页面"""
        print("🌐 加载初始页面...")
        try:
            self.driver.get(self.base_url)
            time.sleep(5)  # 等待页面完全加载
            
            # 保存初始页面源码
            with open("html_sources/shanghai/real_initial_page.html", 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            
            print("✅ 初始页面加载成功")
            return True
        except Exception as e:
            print(f"❌ 初始页面加载失败: {e}")
            return False
    
    def find_page_buttons(self):
        """查找页面上所有的页码按钮"""
        print("🔍 查找页码按钮...")
        
        page_buttons = {}
        button_selectors = [
            # 通用分页选择器
            ".pagination a",
            ".pagination button", 
            ".pager a",
            ".pager button",
            ".page-numbers a",
            ".page-numbers button",
            # 更具体的选择器
            "a[class*='page']",
            "button[class*='page']",
            "span[class*='page']",
            # 数字按钮
            "a[href*='page']",
            "button[data-page]",
            "a[data-page]",
        ]
        
        for selector in button_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    # 获取按钮文本
                    text = elem.text.strip()
                    # 获取data-page属性
                    data_page = elem.get_attribute('data-page')
                    
                    # 检查文本是否为数字
                    if text.isdigit():
                        page_num = int(text)
                        page_buttons[page_num] = elem
                        print(f"  找到页码按钮 {page_num}: {text} (选择器: {selector})")
                    
                    # 检查data-page属性
                    elif data_page and data_page.isdigit():
                        page_num = int(data_page)
                        page_buttons[page_num] = elem
                        print(f"  找到页码按钮 {page_num}: data-page={data_page} (选择器: {selector})")
                        
            except Exception as e:
                continue
        
        # 手动查找数字按钮 (1, 2, 3 等)
        if not page_buttons:
            print("  尝试手动查找数字按钮...")
            for i in range(1, 11):  # 查找1-10页
                xpath_selectors = [
                    f"//a[text()='{i}']",
                    f"//button[text()='{i}']", 
                    f"//span[text()='{i}']",
                    f"//a[contains(@class, 'page') and text()='{i}']",
                    f"//button[contains(@class, 'page') and text()='{i}']",
                    f"//*[contains(@class, 'pagination')]//*[text()='{i}']",
                    f"//*[contains(@class, 'pager')]//*[text()='{i}']"
                ]
                
                for xpath in xpath_selectors:
                    try:
                        elem = self.driver.find_element(By.XPATH, xpath)
                        if elem.is_displayed():
                            page_buttons[i] = elem
                            print(f"  手动找到页码按钮 {i}: {elem.text} (xpath: {xpath})")
                            break
                    except:
                        continue
        
        print(f"🔢 总共找到 {len(page_buttons)} 个页码按钮: {list(page_buttons.keys())}")
        return page_buttons
    
    def click_page_button(self, page_number, page_buttons):
        """点击指定页码按钮"""
        print(f"🖱️ 点击第 {page_number} 页按钮...")
        
        # 如果在已找到的按钮中
        if page_number in page_buttons:
            button = page_buttons[page_number]
            try:
                # 滚动到按钮位置
                self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                time.sleep(1)
                
                # 尝试普通点击
                button.click()
                print(f"  ✅ 成功点击第 {page_number} 页按钮")
                time.sleep(3)  # 等待页面加载
                return True
                
            except Exception as click_error:
                print(f"  普通点击失败，尝试JavaScript点击: {click_error}")
                try:
                    self.driver.execute_script("arguments[0].click();", button)
                    print(f"  ✅ JavaScript点击成功")
                    time.sleep(3)
                    return True
                except Exception as js_error:
                    print(f"  JavaScript点击也失败: {js_error}")
        
        # 如果在已找到的按钮中没有，尝试实时查找
        print(f"  在预存按钮中未找到第 {page_number} 页，尝试实时查找...")
        xpath_selectors = [
            f"//a[text()='{page_number}']",
            f"//button[text()='{page_number}']",
            f"//span[text()='{page_number}']",
            f"//a[contains(@class, 'page') and text()='{page_number}']",
            f"//button[contains(@class, 'page') and text()='{page_number}']",
            f"//*[contains(@class, 'pagination')]//*[text()='{page_number}']",
            f"//a[@data-page='{page_number}']",
            f"//button[@data-page='{page_number}']"
        ]
        
        for xpath in xpath_selectors:
            try:
                button = self.driver.find_element(By.XPATH, xpath)
                if button.is_displayed():
                    # 滚动到按钮位置
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    time.sleep(1)
                    
                    # 尝试点击
                    try:
                        button.click()
                        print(f"  ✅ 实时找到并点击第 {page_number} 页按钮")
                        time.sleep(3)
                        return True
                    except:
                        try:
                            self.driver.execute_script("arguments[0].click();", button)
                            print(f"  ✅ 实时找到并JavaScript点击第 {page_number} 页按钮")
                            time.sleep(3)
                            return True
                        except:
                            continue
            except:
                continue
        
        print(f"  ❌ 未能点击第 {page_number} 页按钮")
        return False
    
    def extract_page_data(self, page_num):
        """提取当前页面的数据"""
        print(f"  📄 提取第 {page_num} 页数据...")
        
        page_datacenters = []
        
        try:
            # 等待页面内容加载
            time.sleep(3)
            
            # 保存页面源码
            with open(f"html_sources/shanghai/real_page_{page_num}.html", 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            
            # 从JavaScript变量中提取数据
            js_commands = [
                "return window.datacenters || [];",
                "return window.locations || [];", 
                "return window.facilities || [];",
                "return window.markers || [];",
                "return window.mapData || [];",
                "return window.sites || [];",
            ]
            
            for cmd in js_commands:
                try:
                    result = self.driver.execute_script(cmd)
                    if result and isinstance(result, list):
                        for item in result:
                            if isinstance(item, dict) and 'latitude' in item and 'longitude' in item:
                                dc = {
                                    'name': item.get('name', item.get('title', f'数据中心_{len(page_datacenters)+1}')),
                                    'latitude': float(item['latitude']),
                                    'longitude': float(item['longitude']),
                                    'location': '上海市',
                                    'source_page': page_num,
                                    'extraction_method': 'JavaScript',
                                    'raw_data': item
                                }
                                
                                # 验证坐标是否在上海范围内
                                if 30.6 <= dc['latitude'] <= 31.9 and 120.8 <= dc['longitude'] <= 122.2:
                                    page_datacenters.append(dc)
                        
                        if result:
                            print(f"    从 {cmd} 获取到 {len([x for x in result if isinstance(x, dict) and 'latitude' in x])} 个坐标数据")
                            break
                except:
                    continue
            
            # 从DOM元素中提取数据
            coord_selectors = [
                '[data-lat]',
                '[data-latitude]',
                '.marker[data-coordinates]',
                '.datacenter-item',
                '.location-item'
            ]
            
            for selector in coord_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        try:
                            lat = elem.get_attribute('data-lat') or elem.get_attribute('data-latitude')
                            lng = elem.get_attribute('data-lng') or elem.get_attribute('data-longitude')
                            
                            if lat and lng:
                                lat, lng = float(lat), float(lng)
                                
                                name = (elem.get_attribute('title') or 
                                       elem.get_attribute('data-name') or
                                       elem.text.strip() or
                                       f"数据中心_{len(page_datacenters)+1}")
                                
                                if 30.6 <= lat <= 31.9 and 120.8 <= lng <= 122.2:
                                    page_datacenters.append({
                                        'name': name,
                                        'latitude': lat,
                                        'longitude': lng,
                                        'location': '上海市',
                                        'source_page': page_num,
                                        'extraction_method': 'DOM',
                                        'raw_data': {
                                            'element_tag': elem.tag_name,
                                            'attributes': {attr: elem.get_attribute(attr) for attr in ['data-lat', 'data-lng', 'title', 'data-name'] if elem.get_attribute(attr)}
                                        }
                                    })
                        except:
                            continue
                except:
                    continue
            
            print(f"    第 {page_num} 页获取到 {len(page_datacenters)} 个数据中心")
            
        except Exception as e:
            print(f"    第 {page_num} 页数据提取失败: {e}")
        
        return page_datacenters
    
    def run_crawler(self):
        """运行爬虫主程序"""
        print("🚀 开始真实页码按钮点击爬虫")
        print("🎯 目标：通过点击页面按钮获取所有数据")
        print("📄 预期：第1页40个，第2页14个，共54个数据中心")
        print("="*70)
        
        if not self.setup_driver():
            return []
        
        try:
            # 1. 加载初始页面
            if not self.load_initial_page():
                return []
            
            # 2. 查找所有页码按钮
            page_buttons = self.find_page_buttons()
            
            if not page_buttons:
                print("❌ 未找到任何页码按钮，尝试获取第一页数据")
                total_pages = 1
            else:
                total_pages = max(page_buttons.keys())
                print(f"📊 检测到总页数: {total_pages}")
            
            # 3. 逐页爬取数据
            all_datacenters = []
            
            for page_num in range(1, total_pages + 1):
                print(f"\n📄 处理第 {page_num} 页 ({page_num}/{total_pages})")
                
                # 如果不是第一页，需要点击页码按钮
                if page_num > 1:
                    success = self.click_page_button(page_num, page_buttons)
                    if not success:
                        print(f"    无法点击第 {page_num} 页按钮，跳过")
                        continue
                
                # 提取当前页面数据
                page_data = self.extract_page_data(page_num)
                if page_data:
                    all_datacenters.extend(page_data)
                    print(f"    ✅ 第 {page_num} 页获取 {len(page_data)} 个数据中心")
                else:
                    print(f"    ❌ 第 {page_num} 页未获取到数据")
                
                # 保存页面数据
                self.page_data[f'page_{page_num}'] = page_data
                
                time.sleep(2)  # 页面间延迟
            
            # 4. 数据去重
            unique_datacenters = self.deduplicate_datacenters(all_datacenters)
            
            print(f"\n{'='*70}")
            print(f"📊 爬取完成统计:")
            print(f"  总页数: {total_pages}")
            print(f"  原始数据: {len(all_datacenters)} 个")
            print(f"  去重后数据: {len(unique_datacenters)} 个")
            
            # 按页统计
            for page_num in range(1, total_pages + 1):
                page_count = len(self.page_data.get(f'page_{page_num}', []))
                print(f"  第 {page_num} 页: {page_count} 个数据中心")
            
            return unique_datacenters
            
        except Exception as e:
            print(f"❌ 爬取过程出错: {e}")
            import traceback
            traceback.print_exc()
            return []
        
        finally:
            if self.driver:
                self.driver.quit()
    
    def deduplicate_datacenters(self, datacenters):
        """去重数据中心"""
        print(f"🔄 数据去重处理...")
        
        unique_datacenters = []
        seen_coords = set()
        
        for dc in datacenters:
            # 基于坐标去重（精确到小数点后5位）
            coord_key = (round(dc['latitude'], 5), round(dc['longitude'], 5))
            
            if coord_key not in seen_coords:
                seen_coords.add(coord_key)
                unique_datacenters.append(dc)
        
        print(f"  去重前: {len(datacenters)} 个")
        print(f"  去重后: {len(unique_datacenters)} 个")
        
        return unique_datacenters
    
    def save_results(self, datacenters):
        """保存结果"""
        if not datacenters:
            print("❌ 没有数据需要保存")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存JSON数据
        json_file = f"data/shanghai/上海数据中心真实按钮点击_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(datacenters, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON文件已保存: {json_file}")
        
        # 保存CSV数据
        csv_file = f"data/shanghai/上海数据中心真实按钮点击_{timestamp}.csv"
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            f.write("序号,名称,纬度,经度,位置,来源页,提取方法\n")
            for i, dc in enumerate(datacenters, 1):
                f.write(f"{i},{dc['name']},{dc['latitude']},{dc['longitude']},{dc['location']},第{dc['source_page']}页,{dc['extraction_method']}\n")
        print(f"✅ CSV文件已保存: {csv_file}")
        
        # 保存分页详情
        page_detail_file = f"data/shanghai/真实按钮翻页详情_{timestamp}.json"
        with open(page_detail_file, 'w', encoding='utf-8') as f:
            json.dump(self.page_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 分页详情已保存: {page_detail_file}")
        
        # 生成详细报告
        self.generate_detailed_report(datacenters, timestamp)
    
    def generate_detailed_report(self, datacenters, timestamp):
        """生成详细报告"""
        report_file = f"data/shanghai/真实按钮点击报告_{timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("上海数据中心真实页码按钮点击爬取报告\n")
            f.write("="*60 + "\n\n")
            
            f.write(f"爬取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"爬取方法: Selenium真实按钮点击\n")
            f.write(f"总数据中心: {len(datacenters)} 个\n")
            f.write(f"目标完成度: {len(datacenters)}/54 ({len(datacenters)/54*100:.1f}%)\n\n")
            
            # 按页统计
            f.write("分页统计:\n")
            f.write("-"*30 + "\n")
            for page_num, page_data in self.page_data.items():
                f.write(f"{page_num}: {len(page_data)} 个数据中心\n")
            f.write("\n")
            
            # 按提取方法统计
            method_stats = {}
            for dc in datacenters:
                method = dc.get('extraction_method', '未知')
                method_stats[method] = method_stats.get(method, 0) + 1
            
            f.write("提取方法统计:\n")
            f.write("-"*30 + "\n")
            for method, count in method_stats.items():
                f.write(f"{method}: {count} 个\n")
            f.write("\n")
            
            # 详细数据列表
            f.write("数据中心详细列表:\n")
            f.write("-"*30 + "\n")
            for i, dc in enumerate(datacenters, 1):
                f.write(f"{i:2d}. {dc['name']}\n")
                f.write(f"    坐标: ({dc['latitude']:.6f}, {dc['longitude']:.6f})\n")
                f.write(f"    来源页: 第{dc['source_page']}页\n")
                f.write(f"    提取方法: {dc['extraction_method']}\n\n")
        
        print(f"✅ 详细报告已保存: {report_file}")

def main():
    """主函数"""
    print("🎯 上海数据中心真实页码按钮点击爬虫")
    print("🖱️ 专门通过Selenium模拟真实点击页面按钮进行翻页")
    print("📄 预期：第1页40个，第2页14个，共54个数据中心")
    
    crawler = RealButtonCrawler()
    
    try:
        # 运行爬虫
        results = crawler.run_crawler()
        
        if results:
            print(f"\n🎉 爬取完成！")
            print(f"✅ 获取到 {len(results)} 个上海数据中心")
            
            # 显示前10个结果
            print(f"\n📋 前10个数据中心:")
            for i, dc in enumerate(results[:10], 1):
                print(f"  {i:2d}. {dc['name']} (第{dc['source_page']}页)")
            
            if len(results) > 10:
                print(f"     ... 还有 {len(results) - 10} 个")
            
            # 保存结果
            crawler.save_results(results)
            
            # 检查是否达到目标
            if len(results) >= 54:
                print(f"\n🎯 目标达成！获取到 {len(results)} 个数据中心 (目标54个)")
            else:
                print(f"\n⚠️ 距离目标还差 {54 - len(results)} 个数据中心")
                print("💡 建议：检查页面按钮是否正确识别和点击")
            
        else:
            print("❌ 未获取到任何数据")
            print("💡 建议：检查页面结构或网络连接")
            
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断爬取")
    except Exception as e:
        print(f"❌ 爬取过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
