#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JavaScript动态翻页爬虫
专门处理在同一URL内通过JavaScript动态切换页面数据的网站
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

class JavaScriptPaginationCrawler:
    def __init__(self):
        self.base_url = "https://www.datacenters.com/locations/china/shanghai"
          # 设置Chrome选项
        self.chrome_options = Options()
        # self.chrome_options.add_argument('--headless')  # 禁用无头模式，便于调试
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
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
    
    def analyze_pagination_structure(self):
        """分析页面的JavaScript翻页结构"""
        print("🔍 分析JavaScript翻页结构...")
        
        try:
            # 加载主页面
            self.driver.get(self.base_url)
            time.sleep(5)  # 等待页面完全加载
            
            # 保存初始页面源码
            with open("html_sources/shanghai/js_initial_page.html", 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            
            # 查找分页相关元素
            pagination_info = self.find_pagination_elements()
            
            # 分析JavaScript中的分页逻辑
            js_pagination_info = self.analyze_javascript_pagination()
            
            return {
                'pagination_elements': pagination_info,
                'javascript_info': js_pagination_info
            }
            
        except Exception as e:
            print(f"❌ 分析翻页结构失败: {e}")
            return None
    
    def find_pagination_elements(self):
        """查找分页相关的DOM元素"""
        pagination_info = {
            'pagination_container': None,
            'page_buttons': [],
            'next_button': None,
            'previous_button': None,
            'page_info': None,
            'total_pages': 0
        }
        
        # 常见的分页元素选择器
        pagination_selectors = [
            '.pagination',
            '.pager',
            '.page-navigation',
            '.paginate',
            '[class*="pagination"]',
            '[class*="pager"]',
            '[id*="pagination"]',
            '[id*="pager"]'
        ]
        
        for selector in pagination_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    pagination_info['pagination_container'] = selector
                    print(f"  找到分页容器: {selector}")
                    break
            except:
                continue
        
        # 查找页面按钮
        page_button_selectors = [
            'a[onclick*="page"]',
            'button[onclick*="page"]',
            '[data-page]',
            '.page-number',
            '.page-btn',
            'a[href*="page"]',
            'button[data-target*="page"]'
        ]
        
        for selector in page_button_selectors:
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if buttons:
                    pagination_info['page_buttons'].extend(buttons)
                    print(f"  找到页面按钮: {len(buttons)} 个 ({selector})")
            except:
                continue
        
        # 查找下一页/上一页按钮
        nav_selectors = {
            'next': ['[onclick*="next"]', 'button:contains("Next")', '.next-page', '[data-action="next"]'],
            'previous': ['[onclick*="prev"]', 'button:contains("Previous")', '.prev-page', '[data-action="prev"]']
        }
        
        for nav_type, selectors in nav_selectors.items():
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element:
                        pagination_info[f'{nav_type}_button'] = element
                        print(f"  找到{nav_type}按钮: {selector}")
                        break
                except:
                    continue
        
        # 尝试获取总页数
        total_page_patterns = [
            r'(?:共|total|of)\s*(\d+)\s*(?:页|pages?)',
            r'(\d+)\s*页',
            r'page\s*\d+\s*of\s*(\d+)',
        ]
        
        page_source = self.driver.page_source
        for pattern in total_page_patterns:
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            if matches:
                try:
                    pagination_info['total_pages'] = int(matches[0])
                    print(f"  检测到总页数: {pagination_info['total_pages']}")
                    break
                except:
                    continue
        
        return pagination_info
    
    def analyze_javascript_pagination(self):
        """分析JavaScript中的分页逻辑"""
        js_info = {
            'pagination_functions': [],
            'ajax_endpoints': [],
            'page_variables': [],
            'event_handlers': []
        }
        
        try:
            # 获取页面中的所有script标签
            scripts = self.driver.find_elements(By.TAG_NAME, 'script')
            
            for script in scripts:
                script_content = script.get_attribute('innerHTML') or ''
                
                # 查找分页相关函数
                function_patterns = [
                    r'function\s+(\w*page\w*)\s*\(',
                    r'(\w*page\w*)\s*:\s*function',
                    r'function\s+(\w*load\w*)\s*\(',
                    r'(\w*navigate\w*)\s*:\s*function'
                ]
                
                for pattern in function_patterns:
                    matches = re.findall(pattern, script_content, re.IGNORECASE)
                    js_info['pagination_functions'].extend(matches)
                
                # 查找AJAX端点
                ajax_patterns = [
                    r'url\s*:\s*["\']([^"\']*(?:page|data|load)[^"\']*)["\']',
                    r'fetch\s*\(\s*["\']([^"\']+)["\']',
                    r'\.get\s*\(\s*["\']([^"\']+)["\']',
                    r'\.post\s*\(\s*["\']([^"\']+)["\']'
                ]
                
                for pattern in ajax_patterns:
                    matches = re.findall(pattern, script_content, re.IGNORECASE)
                    js_info['ajax_endpoints'].extend(matches)
                
                # 查找页面变量
                var_patterns = [
                    r'(?:var|let|const)\s+(\w*page\w*)\s*=',
                    r'(?:var|let|const)\s+(\w*current\w*)\s*=',
                    r'(?:var|let|const)\s+(\w*total\w*)\s*='
                ]
                
                for pattern in var_patterns:
                    matches = re.findall(pattern, script_content, re.IGNORECASE)
                    js_info['page_variables'].extend(matches)
            
            # 去重
            for key in js_info:
                if isinstance(js_info[key], list):
                    js_info[key] = list(set(js_info[key]))
            
            print(f"  JavaScript分页函数: {js_info['pagination_functions']}")
            print(f"  AJAX端点: {js_info['ajax_endpoints']}")
            print(f"  页面变量: {js_info['page_variables']}")            
        except Exception as e:
            print(f"  JavaScript分析出错: {e}")
        
        return js_info
    
    def detect_total_pages(self):
        """检测总页数 - 通过查找页面上的页码按钮"""
        print("🔢 检测总页数...")
        
        total_pages = 0
        
        try:
            # 等待页面完全加载
            time.sleep(3)
            
            # 查找所有可能的页码按钮
            pagination_selectors = [
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
            
            page_numbers = set()
            
            for selector in pagination_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        # 获取按钮文本
                        text = elem.text.strip()
                        # 获取data-page属性
                        data_page = elem.get_attribute('data-page')
                        
                        # 检查文本是否为数字
                        if text.isdigit():
                            page_numbers.add(int(text))
                            print(f"  找到页码按钮: {text} (文本)")
                        
                        # 检查data-page属性
                        if data_page and data_page.isdigit():
                            page_numbers.add(int(data_page))
                            print(f"  找到页码按钮: {data_page} (属性)")
                        
                        # 从href中提取页码
                        href = elem.get_attribute('href')
                        if href:
                            page_match = re.search(r'page[=\-_](\d+)', href, re.IGNORECASE)
                            if page_match:
                                page_numbers.add(int(page_match.group(1)))
                                print(f"  从href找到页码: {page_match.group(1)}")
                                
                except Exception as e:
                    continue
            
            if page_numbers:
                total_pages = max(page_numbers)
                print(f"  从页码按钮检测到总页数: {total_pages}")
            else:
                # 手动查找数字按钮 (1, 2, 3 等)
                print("  尝试手动查找数字按钮...")
                for i in range(1, 11):  # 查找1-10页
                    try:
                        # 尝试多种方式查找数字按钮
                        xpath_selectors = [
                            f"//a[text()='{i}']",
                            f"//button[text()='{i}']", 
                            f"//span[text()='{i}']",
                            f"//a[contains(@class, 'page') and text()='{i}']",
                            f"//button[contains(@class, 'page') and text()='{i}']",
                            f"//*[contains(@class, 'pagination')]//*[text()='{i}']"
                        ]
                        
                        for xpath in xpath_selectors:
                            try:
                                elem = self.driver.find_element(By.XPATH, xpath)
                                if elem.is_displayed():
                                    page_numbers.add(i)
                                    print(f"  手动找到页码按钮: {i}")
                                    break
                            except:
                                continue
                    except:
                        continue
                
                if page_numbers:
                    total_pages = max(page_numbers)
                    print(f"  手动检测到总页数: {total_pages}")
            
            # 如果还是找不到，检查页面源码中的分页信息
            if total_pages == 0:
                print("  检查页面源码中的分页信息...")
                page_source = self.driver.page_source
                
                # 在源码中查找分页相关信息
                patterns = [
                    r'totalPages["\']?\s*:\s*(\d+)',
                    r'pageCount["\']?\s*:\s*(\d+)', 
                    r'total["\']?\s*:\s*(\d+)',
                    r'共\s*(\d+)\s*页',
                    r'Page\s+\d+\s+of\s+(\d+)',
                    r'第\s*\d+\s*页\s*/\s*(\d+)',
                    r'"page"\s*:\s*\d+[^}]*"total"\s*:\s*(\d+)',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, page_source, re.IGNORECASE)
                    if matches:
                        try:
                            total_pages = int(matches[0])
                            print(f"  从源码检测到总页数: {total_pages}")
                            break
                        except:
                            continue
            
        except Exception as e:
            print(f"  检测页数时出错: {e}")
        
        # 如果还是检测不到，根据之前分析默认设为2页
        if total_pages == 0:
            total_pages = 2
            print(f"  使用默认值: {total_pages} 页 (基于之前分析)")
        
        return total_pages
    
    def click_page_button(self, page_number):
        """模拟点击页码按钮"""
        print(f"🖱️ 尝试点击第 {page_number} 页按钮...")
        
        # 多种方式查找页码按钮
        button_selectors = [
            # 通过文本内容查找
            f"//a[text()='{page_number}']",
            f"//button[text()='{page_number}']",
            f"//span[text()='{page_number}']",
            
            # 通过class和文本组合查找
            f"//a[contains(@class, 'page') and text()='{page_number}']",
            f"//button[contains(@class, 'page') and text()='{page_number}']",
            f"//*[contains(@class, 'pagination')]//*[text()='{page_number}']",
            
            # 通过data属性查找
            f"//a[@data-page='{page_number}']",
            f"//button[@data-page='{page_number}']",
            f"//*[@data-page='{page_number}']",
            
            # 通过href属性查找
            f"//a[contains(@href, 'page={page_number}')]",
            f"//a[contains(@href, 'page-{page_number}')]",
            f"//a[contains(@href, 'p{page_number}')]",
        ]
        
        # 尝试每种选择器
        for selector in button_selectors:
            try:
                print(f"  尝试选择器: {selector}")
                button = self.driver.find_element(By.XPATH, selector)
                
                if button and button.is_displayed():
                    print(f"  找到可见按钮: {button.text} / {button.get_attribute('outerHTML')[:100]}...")
                    
                    # 滚动到按钮位置
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    time.sleep(1)
                    
                    # 尝试点击
                    try:
                        button.click()
                        print(f"  ✅ 成功点击第 {page_number} 页按钮")
                        time.sleep(3)  # 等待页面加载
                        return True
                    except Exception as click_error:
                        print(f"  点击失败，尝试JavaScript点击: {click_error}")
                        try:
                            self.driver.execute_script("arguments[0].click();", button)
                            print(f"  ✅ JavaScript点击成功")
                            time.sleep(3)
                            return True
                        except Exception as js_error:
                            print(f"  JavaScript点击也失败: {js_error}")
                            continue
                            
            except Exception as e:
                print(f"  选择器 {selector} 失败: {e}")
                continue
        
        print(f"  ❌ 未能找到或点击第 {page_number} 页按钮")
        return False
    
    def extract_page_data(self, page_num):
        """提取当前页面的数据"""
        print(f"  📄 提取第 {page_num} 页数据...")
        
        page_datacenters = []
        
        try:
            # 等待页面内容加载
            time.sleep(3)
            
            # 保存页面源码
            with open(f"html_sources/shanghai/js_page_{page_num}.html", 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            
            # 提取方法1: 从JavaScript变量中提取
            script_data = self.extract_from_javascript(page_num)
            if script_data:
                page_datacenters.extend(script_data)
            
            # 提取方法2: 从DOM元素中提取
            dom_data = self.extract_from_dom(page_num)
            if dom_data:
                page_datacenters.extend(dom_data)
            
            # 提取方法3: 从网络请求中提取（监听AJAX）
            network_data = self.extract_from_network(page_num)
            if network_data:
                page_datacenters.extend(network_data)
            
            print(f"    第 {page_num} 页获取到 {len(page_datacenters)} 个数据中心")
            
        except Exception as e:
            print(f"    第 {page_num} 页数据提取失败: {e}")
        
        return page_datacenters
    
    def extract_from_javascript(self, page_num):
        """从JavaScript变量中提取数据"""
        datacenters = []
        
        try:
            # 执行JavaScript获取页面数据
            js_commands = [
                "return window.datacenters || [];",
                "return window.locations || [];", 
                "return window.facilities || [];",
                "return window.markers || [];",
                "return window.mapData || [];",
            ]
            
            for cmd in js_commands:
                try:
                    result = self.driver.execute_script(cmd)
                    if result and isinstance(result, list):
                        for item in result:
                            if isinstance(item, dict) and 'latitude' in item and 'longitude' in item:
                                dc = {
                                    'name': item.get('name', item.get('title', f'数据中心_{len(datacenters)+1}')),
                                    'latitude': float(item['latitude']),
                                    'longitude': float(item['longitude']),
                                    'location': '上海市',
                                    'source_page': page_num,
                                    'extraction_method': 'JavaScript',
                                    'raw_data': item
                                }
                                
                                # 验证坐标是否在上海范围内
                                if 30.6 <= dc['latitude'] <= 31.9 and 120.8 <= dc['longitude'] <= 122.2:
                                    datacenters.append(dc)
                        
                        if result:
                            break  # 找到数据就停止
                except:
                    continue
            
        except Exception as e:
            print(f"      JavaScript提取失败: {e}")
        
        return datacenters
    
    def extract_from_dom(self, page_num):
        """从DOM元素中提取数据"""
        datacenters = []
        
        try:
            # 查找包含坐标信息的元素
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
                                       f"数据中心_{len(datacenters)+1}")
                                
                                if 30.6 <= lat <= 31.9 and 120.8 <= lng <= 122.2:
                                    datacenters.append({
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
            
        except Exception as e:
            print(f"      DOM提取失败: {e}")
        
        return datacenters
    
    def extract_from_network(self, page_num):
        """从网络请求中提取数据（尝试获取AJAX响应）"""
        datacenters = []
        
        try:
            # 这里可以添加网络监听逻辑
            # 由于Selenium的限制，我们主要依靠前两种方法
            pass
        except Exception as e:
            print(f"      网络提取失败: {e}")
        
        return datacenters
    
    def navigate_to_page(self, page_num):
        """导航到指定页面 - 使用真实按钮点击"""
        print(f"  🔄 导航到第 {page_num} 页...")
        
        # 使用专门的按钮点击方法
        return self.click_page_button(page_num)
    
    def crawl_all_pages(self):
        """爬取所有页面"""
        print("🚀 开始JavaScript动态翻页爬虫")
        print("🎯 目标：获取所有页面的数据中心信息")
        print("="*70)
        
        if not self.setup_driver():
            return []
        
        try:
            # 1. 分析翻页结构
            structure = self.analyze_pagination_structure()
            
            # 2. 检测总页数
            total_pages = self.detect_total_pages()
            print(f"📊 检测到总页数: {total_pages}")
            
            # 3. 逐页爬取数据
            all_datacenters = []
            
            for page_num in range(1, total_pages + 1):
                print(f"\n📄 处理第 {page_num} 页 ({page_num}/{total_pages})")
                
                # 导航到页面
                if page_num == 1:
                    # 第一页已经加载
                    pass
                else:
                    success = self.navigate_to_page(page_num)
                    if not success:
                        print(f"    无法导航到第 {page_num} 页，跳过")
                        continue
                
                # 提取页面数据
                page_data = self.extract_page_data(page_num)
                if page_data:
                    all_datacenters.extend(page_data)
                    print(f"    ✅ 第 {page_num} 页获取 {len(page_data)} 个数据中心")
                else:
                    print(f"    ❌ 第 {page_num} 页未获取到数据")
                
                # 保存页面数据
                self.page_data[f'page_{page_num}'] = page_data
                
                time.sleep(2)  # 页面间延迟
            
            # 4. 去重处理
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
        json_file = f"data/shanghai/上海数据中心JS翻页_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(datacenters, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON文件已保存: {json_file}")
        
        # 保存分页详情
        page_detail_file = f"data/shanghai/翻页详情_{timestamp}.json"
        with open(page_detail_file, 'w', encoding='utf-8') as f:
            json.dump(self.page_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 分页详情已保存: {page_detail_file}")
        
        # 生成详细报告
        self.generate_detailed_report(datacenters, timestamp)
    
    def generate_detailed_report(self, datacenters, timestamp):
        """生成详细报告"""
        report_file = f"data/shanghai/JS翻页爬取报告_{timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("上海数据中心JavaScript翻页爬取报告\n")
            f.write("="*60 + "\n\n")
            
            f.write(f"爬取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"爬取方法: JavaScript动态翻页\n")
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
    print("🎯 上海数据中心JavaScript动态翻页爬虫")
    print("🔄 专门处理同一URL内的JavaScript翻页")
    print("📄 预期：第1页40个，第2页14个，共54个数据中心")
    
    crawler = JavaScriptPaginationCrawler()
    
    try:
        # 运行爬虫
        results = crawler.crawl_all_pages()
        
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
            
        else:
            print("❌ 未获取到任何数据")
            
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断爬取")
    except Exception as e:
        print(f"❌ 爬取过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
