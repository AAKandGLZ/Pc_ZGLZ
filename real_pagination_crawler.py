#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Selenium真实翻页爬虫
模拟点击页面按钮进行翻页，获取每页真实数据
"""

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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

class RealPaginationCrawler:
    def __init__(self):
        self.base_url = "https://www.datacenters.com/locations/china/shanghai"
        
        # 设置Chrome选项
        self.chrome_options = Options()
        # 先不使用无头模式，方便调试
        # self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = None
        self.wait = None
        self.all_datacenters = []
        self.page_data = {}
        
        # 创建输出目录
        os.makedirs("data/shanghai", exist_ok=True)
        os.makedirs("html_sources/shanghai", exist_ok=True)
    
    def setup_driver(self):
        """初始化WebDriver"""
        try:
            # 尝试初始化Chrome WebDriver
            print("🔧 初始化Chrome WebDriver...")
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.implicitly_wait(10)
            self.wait = WebDriverWait(self.driver, 15)
            print("✅ WebDriver初始化成功")
            return True
        except Exception as e:
            print(f"❌ WebDriver初始化失败: {e}")
            print("💡 请确保已安装Chrome浏览器和ChromeDriver")
            return False
    
    def load_page_and_wait(self):
        """加载页面并等待内容加载完成"""
        print("📄 加载主页面...")
        
        try:
            self.driver.get(self.base_url)
            print("  页面已加载，等待内容渲染...")
            
            # 等待页面主要内容加载
            time.sleep(5)
            
            # 等待地图或数据加载完成
            try:
                # 等待某个关键元素出现
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                print("  ✅ 页面内容加载完成")
            except TimeoutException:
                print("  ⚠️ 页面加载超时，但继续执行")
            
            return True
            
        except Exception as e:
            print(f"  ❌ 页面加载失败: {e}")
            return False
    
    def find_pagination_elements(self):
        """找到页面上的翻页元素"""
        print("🔍 查找翻页元素...")
        
        pagination_info = {
            'total_pages': 0,
            'page_buttons': [],
            'next_button': None,
            'current_page': 1
        }
        
        # 保存当前页面HTML用于分析
        with open("html_sources/shanghai/pagination_analysis.html", 'w', encoding='utf-8') as f:
            f.write(self.driver.page_source)
        
        # 查找页面按钮的多种方式
        page_button_patterns = [
            # 直接查找包含数字的按钮或链接
            "//a[contains(@class, 'page') and text()='2']",
            "//button[contains(@class, 'page') and text()='2']",
            "//a[contains(@href, 'page') and text()='2']",
            
            # 查找分页容器中的数字按钮
            "//*[contains(@class, 'pagination')]//a[text()='2']",
            "//*[contains(@class, 'pager')]//a[text()='2']",
            "//*[contains(@class, 'page')]//a[text()='2']",
            
            # 通过onclick或其他属性查找
            "//a[contains(@onclick, 'page') and text()='2']",
            "//button[contains(@onclick, 'page') and text()='2']",
            
            # 通过data属性查找
            "//a[@data-page='2']",
            "//button[@data-page='2']",
            "//*[@data-page='2']",
        ]
        
        # 尝试找到第2页按钮（作为测试）
        second_page_button = None
        for pattern in page_button_patterns:
            try:
                elements = self.driver.find_elements(By.XPATH, pattern)
                if elements:
                    second_page_button = elements[0]
                    print(f"  ✅ 找到第2页按钮: {pattern}")
                    break
            except:
                continue
        
        if second_page_button:
            # 如果找到了第2页按钮，尝试找所有页面按钮
            try:
                # 基于找到的模式，查找所有页面按钮
                all_page_patterns = [
                    "//a[contains(@class, 'page') and string-length(text())=1 and number(text())=text()]",
                    "//*[contains(@class, 'pagination')]//a[string-length(text())=1 and number(text())=text()]",
                    "//a[@data-page]",
                    "//*[@data-page and string-length(@data-page)=1]"
                ]
                
                for pattern in all_page_patterns:
                    try:
                        elements = self.driver.find_elements(By.XPATH, pattern)
                        if elements:
                            page_numbers = []
                            for elem in elements:
                                try:
                                    # 尝试从文本获取页码
                                    text = elem.text.strip()
                                    if text.isdigit():
                                        page_numbers.append(int(text))
                                    
                                    # 尝试从data-page属性获取页码
                                    data_page = elem.get_attribute('data-page')
                                    if data_page and data_page.isdigit():
                                        page_numbers.append(int(data_page))
                                except:
                                    continue
                              if page_numbers:
                                pagination_info['total_pages'] = max(page_numbers)
                                pagination_info['page_buttons'] = elements
                                print(f"  ✅ 总页数: {pagination_info['total_pages']}")
                                print(f"  ✅ 找到页面按钮: {len(elements)} 个")
                                break
                    except Exception:
                        continue
        
        # 查找"下一页"按钮
        next_button_patterns = [
            "//a[contains(text(), 'Next')]",
            "//button[contains(text(), 'Next')]",
            "//a[contains(@class, 'next')]",
            "//button[contains(@class, 'next')]",
            "//*[contains(@onclick, 'next')]",
            "//a[contains(text(), '下一页')]",
            "//a[contains(text(), '>')]"
        ]
        
        for pattern in next_button_patterns:
            try:
                element = self.driver.find_element(By.XPATH, pattern)
                if element:
                    pagination_info['next_button'] = element
                    print(f"  ✅ 找到下一页按钮: {pattern}")
                    break
            except:
                continue
        
        # 如果没找到具体页数，设置默认值
        if pagination_info['total_pages'] == 0:
            pagination_info['total_pages'] = 2  # 根据之前分析设置默认值
            print(f"  ⚠️ 未找到具体页数，使用默认值: {pagination_info['total_pages']}")
        
        return pagination_info
    
    def extract_current_page_data(self, page_num):
        """提取当前页面的数据"""
        print(f"  📊 提取第 {page_num} 页数据...")
        
        datacenters = []
        
        try:
            # 等待页面加载完成
            time.sleep(3)
            
            # 保存当前页面HTML
            with open(f"html_sources/shanghai/page_{page_num}.html", 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            
            # 方法1: 从JavaScript变量中提取数据
            js_data = self.extract_from_javascript_vars(page_num)
            if js_data:
                datacenters.extend(js_data)
                print(f"    JavaScript变量提取: {len(js_data)} 个")
            
            # 方法2: 从页面源码的正则匹配提取
            regex_data = self.extract_from_page_source(page_num)
            if regex_data:
                datacenters.extend(regex_data)
                print(f"    正则匹配提取: {len(regex_data)} 个")
            
            # 方法3: 从DOM元素提取
            dom_data = self.extract_from_dom_elements(page_num)
            if dom_data:
                datacenters.extend(dom_data)
                print(f"    DOM元素提取: {len(dom_data)} 个")
            
            # 去重当前页面数据
            unique_datacenters = self.deduplicate_page_data(datacenters)
            
            print(f"    ✅ 第 {page_num} 页总计: {len(unique_datacenters)} 个数据中心")
            return unique_datacenters
            
        except Exception as e:
            print(f"    ❌ 第 {page_num} 页数据提取失败: {e}")
            return []
    
    def extract_from_javascript_vars(self, page_num):
        """从JavaScript变量中提取数据"""
        datacenters = []
        
        try:
            # 尝试执行不同的JavaScript命令获取数据
            js_commands = [
                "return window.datacenters || [];",
                "return window.locations || [];",
                "return window.facilities || [];",
                "return window.markers || [];",
                "return window.mapData || [];",
                "return window.map_data || [];",
                "return window.data || [];",
            ]
            
            for cmd in js_commands:
                try:
                    result = self.driver.execute_script(cmd)
                    if result and isinstance(result, list) and len(result) > 0:
                        for item in result:
                            if isinstance(item, dict):
                                lat = item.get('latitude') or item.get('lat') or item.get('y')
                                lng = item.get('longitude') or item.get('lng') or item.get('x')
                                
                                if lat and lng:
                                    try:
                                        lat, lng = float(lat), float(lng)
                                        if 30.6 <= lat <= 31.9 and 120.8 <= lng <= 122.2:
                                            name = item.get('name') or item.get('title') or f"数据中心_{len(datacenters)+1}"
                                            
                                            datacenters.append({
                                                'name': name,
                                                'latitude': lat,
                                                'longitude': lng,
                                                'location': '上海市',
                                                'source_page': page_num,
                                                'extraction_method': 'JavaScript',
                                                'raw_data': item
                                            })
                                    except ValueError:
                                        continue
                        
                        if datacenters:
                            break  # 找到数据就停止尝试其他命令
                except:
                    continue
                    
        except Exception as e:
            pass
        
        return datacenters
    
    def extract_from_page_source(self, page_num):
        """从页面源码中通过正则表达式提取数据"""
        datacenters = []
        
        try:
            page_source = self.driver.page_source
            
            # 多种正则模式提取坐标和名称
            patterns = [
                # JSON格式数据
                r'"latitude":\s*([\d\.-]+).*?"longitude":\s*([\d\.-]+).*?"name":\s*"([^"]*)"',
                r'"lat":\s*([\d\.-]+).*?"lng":\s*([\d\.-]+).*?"title":\s*"([^"]*)"',
                r'"y":\s*([\d\.-]+).*?"x":\s*([\d\.-]+).*?"name":\s*"([^"]*)"',
                
                # JavaScript对象格式
                r'latitude:\s*([\d\.-]+).*?longitude:\s*([\d\.-]+).*?name:\s*["\']([^"\']*)["\']',
                r'lat:\s*([\d\.-]+).*?lng:\s*([\d\.-]+).*?title:\s*["\']([^"\']*)["\']',
                
                # 数组格式
                r'\[([\d\.-]+),\s*([\d\.-]+)\].*?"([^"]*(?:Data Center|IDC|数据中心)[^"]*)"',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_source, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    try:
                        lat, lng, name = float(match[0]), float(match[1]), match[2].strip()
                        
                        # 验证坐标范围
                        if 30.6 <= lat <= 31.9 and 120.8 <= lng <= 122.2:
                            datacenters.append({
                                'name': name or f"数据中心_{len(datacenters)+1}",
                                'latitude': lat,
                                'longitude': lng,
                                'location': '上海市',
                                'source_page': page_num,
                                'extraction_method': 'Regex',
                                'raw_data': {
                                    'pattern': pattern,
                                    'match': match
                                }
                            })
                    except (ValueError, IndexError):
                        continue
                
                # 如果某个模式找到了数据，可以继续尝试其他模式以获取更多数据
        
        except Exception as e:
            pass
        
        return datacenters
    
    def extract_from_dom_elements(self, page_num):
        """从DOM元素中提取数据"""
        datacenters = []
        
        try:
            # 查找包含坐标信息的DOM元素
            selectors = [
                '[data-lat][data-lng]',
                '[data-latitude][data-longitude]',
                '.marker[data-coordinates]',
                '.location[data-lat]',
                '.datacenter[data-coordinates]'
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        try:
                            lat = elem.get_attribute('data-lat') or elem.get_attribute('data-latitude')
                            lng = elem.get_attribute('data-lng') or elem.get_attribute('data-longitude')
                            
                            if lat and lng:
                                lat, lng = float(lat), float(lng)
                                
                                if 30.6 <= lat <= 31.9 and 120.8 <= lng <= 122.2:
                                    name = (elem.get_attribute('title') or 
                                           elem.get_attribute('data-name') or
                                           elem.text.strip() or
                                           f"数据中心_{len(datacenters)+1}")
                                    
                                    datacenters.append({
                                        'name': name,
                                        'latitude': lat,
                                        'longitude': lng,
                                        'location': '上海市',
                                        'source_page': page_num,
                                        'extraction_method': 'DOM',
                                        'raw_data': {
                                            'tag': elem.tag_name,
                                            'attributes': elem.get_attribute('outerHTML')[:200]
                                        }
                                    })
                        except (ValueError, TypeError):
                            continue
                except:
                    continue
        
        except Exception as e:
            pass
        
        return datacenters
    
    def deduplicate_page_data(self, datacenters):
        """去重单页数据"""
        unique_datacenters = []
        seen_coords = set()
        
        for dc in datacenters:
            coord_key = (round(dc['latitude'], 5), round(dc['longitude'], 5))
            if coord_key not in seen_coords:
                seen_coords.add(coord_key)
                unique_datacenters.append(dc)
        
        return unique_datacenters
    
    def click_next_page(self, target_page, pagination_info):
        """点击到指定页面"""
        print(f"  🖱️ 点击到第 {target_page} 页...")
        
        try:
            # 方法1: 直接点击页面按钮
            if pagination_info['page_buttons']:
                for button in pagination_info['page_buttons']:
                    try:
                        button_text = button.text.strip()
                        data_page = button.get_attribute('data-page')
                        
                        if (button_text == str(target_page) or 
                            data_page == str(target_page)):
                            
                            # 滚动到按钮位置
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                            time.sleep(1)
                            
                            # 点击按钮
                            self.driver.execute_script("arguments[0].click();", button)
                            print(f"    ✅ 已点击第 {target_page} 页按钮")
                            
                            # 等待页面加载
                            time.sleep(5)
                            return True
                    except Exception as e:
                        continue
            
            # 方法2: 使用下一页按钮
            if pagination_info['next_button'] and target_page == 2:
                try:
                    # 滚动到下一页按钮
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", pagination_info['next_button'])
                    time.sleep(1)
                    
                    # 点击下一页
                    self.driver.execute_script("arguments[0].click();", pagination_info['next_button'])
                    print(f"    ✅ 已点击下一页按钮")
                    
                    # 等待页面加载
                    time.sleep(5)
                    return True
                except Exception as e:
                    print(f"    ❌ 点击下一页失败: {e}")
            
            # 方法3: 尝试直接执行JavaScript翻页
            js_functions = [
                f"goToPage({target_page})",
                f"loadPage({target_page})", 
                f"showPage({target_page})",
                f"setPage({target_page})",
                f"page = {target_page}; loadData()",
            ]
            
            for func in js_functions:
                try:
                    self.driver.execute_script(func)
                    time.sleep(3)
                    print(f"    ✅ 执行JavaScript: {func}")
                    return True
                except:
                    continue
            
            print(f"    ❌ 无法导航到第 {target_page} 页")
            return False
            
        except Exception as e:
            print(f"    ❌ 翻页失败: {e}")
            return False
    
    def run_real_pagination_crawl(self):
        """运行真实翻页爬虫"""
        print("🚀 上海数据中心真实翻页爬虫启动")
        print("🎯 目标：通过点击页面按钮获取所有页面数据")
        print("="*70)
        
        if not self.setup_driver():
            return []
        
        try:
            # 1. 加载主页面
            if not self.load_page_and_wait():
                return []
            
            # 2. 查找翻页元素
            pagination_info = self.find_pagination_elements()
            total_pages = pagination_info['total_pages']
            
            print(f"📊 检测到总页数: {total_pages}")
            
            if total_pages == 0:
                print("❌ 未检测到翻页元素")
                return []
            
            # 3. 逐页爬取数据
            all_datacenters = []
            
            for page_num in range(1, total_pages + 1):
                print(f"\n📄 处理第 {page_num} 页 ({page_num}/{total_pages})")
                
                # 如果不是第一页，需要翻页
                if page_num > 1:
                    success = self.click_next_page(page_num, pagination_info)
                    if not success:
                        print(f"    ❌ 无法翻到第 {page_num} 页")
                        continue
                
                # 提取当前页数据
                page_data = self.extract_current_page_data(page_num)
                
                if page_data:
                    all_datacenters.extend(page_data)
                    self.page_data[f'page_{page_num}'] = page_data
                    print(f"    ✅ 第 {page_num} 页成功获取 {len(page_data)} 个数据中心")
                else:
                    print(f"    ⚠️ 第 {page_num} 页未获取到数据")
                    self.page_data[f'page_{page_num}'] = []
                
                # 页面间延迟
                time.sleep(2)
            
            # 4. 最终去重
            unique_datacenters = self.final_deduplicate(all_datacenters)
            
            # 5. 输出统计信息
            print(f"\n{'='*70}")
            print(f"📊 真实翻页爬取完成:")
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
                print("🔚 WebDriver已关闭")
    
    def final_deduplicate(self, datacenters):
        """最终去重处理"""
        print(f"🔄 最终去重处理...")
        
        unique_datacenters = []
        seen_coords = set()
        
        for dc in datacenters:
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
        json_file = f"data/shanghai/上海数据中心真实翻页_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(datacenters, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON文件已保存: {json_file}")
        
        # 保存分页详情
        page_detail_file = f"data/shanghai/真实翻页详情_{timestamp}.json"
        with open(page_detail_file, 'w', encoding='utf-8') as f:
            json.dump(self.page_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 分页详情已保存: {page_detail_file}")
        
        # 生成报告
        self.generate_report(datacenters, timestamp)
    
    def generate_report(self, datacenters, timestamp):
        """生成详细报告"""
        report_file = f"data/shanghai/真实翻页爬取报告_{timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("上海数据中心真实翻页爬取报告\n")
            f.write("="*60 + "\n\n")
            
            f.write(f"爬取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"爬取方法: Selenium真实点击翻页\n")
            f.write(f"总数据中心: {len(datacenters)} 个\n")
            f.write(f"目标完成度: {len(datacenters)}/54 ({len(datacenters)/54*100:.1f}%)\n\n")
            
            # 按页统计
            f.write("分页统计:\n")
            f.write("-"*30 + "\n")
            for page_key, page_data in self.page_data.items():
                f.write(f"{page_key}: {len(page_data)} 个数据中心\n")
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
    print("🎯 上海数据中心真实翻页爬虫")
    print("🖱️ 通过Selenium模拟点击页面按钮实现翻页")
    print("📄 目标：第1页40个，第2页14个，共54个数据中心")
    
    crawler = RealPaginationCrawler()
    
    try:
        # 运行真实翻页爬虫
        results = crawler.run_real_pagination_crawl()
        
        if results:
            print(f"\n🎉 真实翻页爬取完成！")
            print(f"✅ 获取到 {len(results)} 个上海数据中心")
            
            # 显示前10个结果预览
            print(f"\n📋 前10个数据中心预览:")
            for i, dc in enumerate(results[:10], 1):
                print(f"  {i:2d}. {dc['name']} (第{dc['source_page']}页, {dc['extraction_method']})")
            
            if len(results) > 10:
                print(f"     ... 还有 {len(results) - 10} 个")
            
            # 保存结果
            crawler.save_results(results)
            
            # 检查目标达成情况
            if len(results) >= 54:
                print(f"\n🎯 目标达成！获取到 {len(results)} 个数据中心 (目标54个)")
            else:
                print(f"\n⚠️ 距离目标还差 {54 - len(results)} 个数据中心")
                print(f"📋 当前获取: {len(results)}/54")
            
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
