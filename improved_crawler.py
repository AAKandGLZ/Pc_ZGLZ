#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上海数据中心真实按钮点击爬虫 - 改进版
基于测试成功的按钮点击技术，应用到真实网站
增加了网络连接重试和错误处理
"""

import time
import os
import json
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

class ShanghaiDatacenterCrawler:
    def __init__(self):
        self.base_url = "https://www.datacenters.com/locations/china/shanghai"
        
        # 设置Chrome选项
        self.chrome_options = Options()
        # 不使用无头模式，便于调试网络问题
        # self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 网络相关配置
        self.chrome_options.add_argument('--ignore-certificate-errors')
        self.chrome_options.add_argument('--ignore-ssl-errors')
        self.chrome_options.add_argument('--allow-running-insecure-content')
        self.chrome_options.add_argument('--disable-web-security')
        self.chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        # 增加超时时间
        self.chrome_options.add_argument('--timeout=30')
        self.chrome_options.add_argument('--page-load-strategy=eager')
        
        self.driver = None
        self.all_datacenters = []
        self.page_data = {}
        
        # 创建输出目录
        os.makedirs("data/shanghai", exist_ok=True)
        os.makedirs("html_sources/shanghai", exist_ok=True)
    
    def test_network_connection(self):
        """测试网络连接"""
        print("🌐 测试网络连接...")
        
        test_urls = [
            "https://www.google.com",
            "https://www.baidu.com", 
            "https://httpbin.org/get",
            self.base_url
        ]
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=10, verify=False)
                print(f"  ✅ {url} - 状态码: {response.status_code}")
                if url == self.base_url:
                    return True
            except Exception as e:
                print(f"  ❌ {url} - 错误: {e}")
        
        return False
    
    def setup_driver(self):
        """初始化WebDriver"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            print("✅ WebDriver初始化成功")
            return True
        except Exception as e:
            print(f"❌ WebDriver初始化失败: {e}")
            return False
    
    def load_page_with_retry(self, max_retries=3):
        """带重试的页面加载"""
        print(f"🌐 加载目标页面 (最多重试{max_retries}次)...")
        
        for attempt in range(max_retries):
            try:
                print(f"  尝试 {attempt + 1}/{max_retries}: {self.base_url}")
                self.driver.get(self.base_url)
                
                # 等待页面加载
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # 保存页面源码
                with open("html_sources/shanghai/improved_initial_page.html", 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                
                print("  ✅ 页面加载成功")
                return True
                
            except TimeoutException:
                print(f"  ⏰ 第{attempt + 1}次尝试超时")
                if attempt < max_retries - 1:
                    time.sleep(5)  # 等待5秒后重试
                    
            except Exception as e:
                print(f"  ❌ 第{attempt + 1}次尝试失败: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
        
        print("❌ 所有尝试都失败了")
        return False
    
    def analyze_page_structure(self):
        """分析页面结构"""
        print("🔍 分析页面结构...")
        
        try:
            # 分析页面总体结构
            title = self.driver.title
            print(f"  页面标题: {title}")
            
            # 查找可能的分页元素
            pagination_selectors = [
                ".pagination", ".pager", ".page-navigation", ".paginate",
                "[class*='pagination']", "[class*='pager']", 
                "[id*='pagination']", "[id*='pager']"
            ]
            
            pagination_found = False
            for selector in pagination_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"  找到分页容器: {selector} ({len(elements)}个)")
                        pagination_found = True
                except:
                    continue
            
            if not pagination_found:
                print("  ⚠️ 未找到明显的分页容器")
            
            # 查找数据容器
            data_selectors = [
                "[data-lat]", "[data-latitude]", ".marker", ".location",
                ".datacenter", ".facility", ".site"
            ]
            
            data_found = False
            for selector in data_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"  找到数据元素: {selector} ({len(elements)}个)")
                        data_found = True
                except:
                    continue
            
            if not data_found:
                print("  ⚠️ 未找到明显的数据元素")
            
            # 检查JavaScript变量
            js_vars_to_check = [
                "window.datacenters", "window.locations", "window.facilities",
                "window.markers", "window.mapData", "window.sites"
            ]
            
            for var in js_vars_to_check:
                try:
                    result = self.driver.execute_script(f"return {var};")
                    if result:
                        print(f"  找到JS变量: {var} (类型: {type(result)}, 长度: {len(result) if isinstance(result, (list, dict)) else 'N/A'})")
                except:
                    continue
            
            return True
            
        except Exception as e:
            print(f"  页面结构分析失败: {e}")
            return False
    
    def find_page_buttons_advanced(self):
        """高级页码按钮查找"""
        print("🔍 高级页码按钮查找...")
        
        page_buttons = {}
        
        # 方法1: 通过onclick属性查找
        try:
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "[onclick*='page'], [onclick*='Page']")
            for btn in buttons:
                text = btn.text.strip()
                if text.isdigit():
                    page_num = int(text)
                    page_buttons[page_num] = btn
                    print(f"  方法1 - 找到页码按钮 {page_num}: {btn.get_attribute('onclick')}")
        except Exception as e:
            print(f"  方法1失败: {e}")
        
        # 方法2: 通过href属性查找
        try:
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='page'], a[href*='Page']")
            for link in links:
                text = link.text.strip()
                if text.isdigit():
                    page_num = int(text)
                    if page_num not in page_buttons:
                        page_buttons[page_num] = link
                        print(f"  方法2 - 找到页码链接 {page_num}: {link.get_attribute('href')}")
        except Exception as e:
            print(f"  方法2失败: {e}")
        
        # 方法3: 通过data属性查找
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-page]")
            for elem in elements:
                data_page = elem.get_attribute('data-page')
                if data_page and data_page.isdigit():
                    page_num = int(data_page)
                    if page_num not in page_buttons:
                        page_buttons[page_num] = elem
                        print(f"  方法3 - 找到页码元素 {page_num}: data-page={data_page}")
        except Exception as e:
            print(f"  方法3失败: {e}")
        
        # 方法4: 通过XPath查找数字按钮
        for i in range(1, 11):  # 查找1-10页
            xpath_selectors = [
                f"//a[text()='{i}']",
                f"//button[text()='{i}']",
                f"//span[text()='{i}']",
                f"//*[contains(@class, 'page') and text()='{i}']",
                f"//*[contains(@class, 'pagination')]//*[text()='{i}']"
            ]
            
            for xpath in xpath_selectors:
                try:
                    elem = self.driver.find_element(By.XPATH, xpath)
                    if elem.is_displayed() and i not in page_buttons:
                        page_buttons[i] = elem
                        print(f"  方法4 - XPath找到页码 {i}: {xpath}")
                        break
                except:
                    continue
        
        print(f"🔢 总共找到 {len(page_buttons)} 个页码按钮: {list(page_buttons.keys())}")
        return page_buttons
    
    def click_page_button_robust(self, page_number, page_buttons):
        """健壮的页码按钮点击"""
        print(f"🖱️ 点击第 {page_number} 页按钮...")
        
        if page_number not in page_buttons:
            print(f"  ❌ 未找到第 {page_number} 页按钮")
            return False
        
        button = page_buttons[page_number]
        
        try:
            # 确保按钮可见
            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
            time.sleep(1)
            
            # 检查按钮状态
            if not button.is_displayed():
                print(f"  ❌ 按钮不可见")
                return False
            
            if not button.is_enabled():
                print(f"  ❌ 按钮不可点击")
                return False
            
            # 尝试多种点击方式
            click_methods = [
                ("普通点击", lambda: button.click()),
                ("JavaScript点击", lambda: self.driver.execute_script("arguments[0].click();", button)),
                ("动作链点击", lambda: webdriver.ActionChains(self.driver).click(button).perform())
            ]
            
            for method_name, method_func in click_methods:
                try:
                    method_func()
                    print(f"  ✅ {method_name}成功")
                    time.sleep(3)  # 等待页面响应
                    return True
                except Exception as e:
                    print(f"  {method_name}失败: {e}")
                    continue
            
            print(f"  ❌ 所有点击方法都失败了")
            return False
            
        except Exception as e:
            print(f"  ❌ 点击过程出错: {e}")
            return False
    
    def extract_data_comprehensive(self, page_num):
        """综合数据提取"""
        print(f"  📄 提取第 {page_num} 页数据...")
        
        datacenters = []
        
        try:
            # 等待页面稳定
            time.sleep(3)
            
            # 保存当前页面源码
            with open(f"html_sources/shanghai/improved_page_{page_num}.html", 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            
            # 方法1: 从JavaScript变量提取
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
                            if isinstance(item, dict) and ('latitude' in item or 'lat' in item) and ('longitude' in item or 'lng' in item):
                                lat = item.get('latitude', item.get('lat'))
                                lng = item.get('longitude', item.get('lng'))
                                
                                if lat and lng:
                                    dc = {
                                        'name': item.get('name', item.get('title', f'数据中心_{len(datacenters)+1}')),
                                        'latitude': float(lat),
                                        'longitude': float(lng),
                                        'location': '上海市',
                                        'source_page': page_num,
                                        'extraction_method': 'JavaScript',
                                        'raw_data': item
                                    }
                                    
                                    # 验证坐标是否在上海范围内
                                    if 30.6 <= dc['latitude'] <= 31.9 and 120.8 <= dc['longitude'] <= 122.2:
                                        datacenters.append(dc)
                        
                        if result:
                            print(f"    从 {cmd} 获取到 {len([x for x in result if isinstance(x, dict) and ('latitude' in x or 'lat' in x)])} 个坐标数据")
                            break
                except:
                    continue
            
            # 方法2: 从DOM元素提取
            coord_selectors = [
                '[data-lat][data-lng]',
                '[data-latitude][data-longitude]',
                '.marker[data-coordinates]',
                '.datacenter-item',
                '.location-item'
            ]
            
            for selector in coord_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        try:
                            lat = (elem.get_attribute('data-lat') or 
                                  elem.get_attribute('data-latitude'))
                            lng = (elem.get_attribute('data-lng') or 
                                  elem.get_attribute('data-longitude'))
                            
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
                                            'selector': selector,
                                            'attributes': {attr: elem.get_attribute(attr) for attr in ['data-lat', 'data-lng', 'title', 'data-name'] if elem.get_attribute(attr)}
                                        }
                                    })
                        except:
                            continue
                except:
                    continue
            
            print(f"    第 {page_num} 页获取到 {len(datacenters)} 个数据中心")
            
        except Exception as e:
            print(f"    第 {page_num} 页数据提取失败: {e}")
        
        return datacenters
    
    def run_crawler(self):
        """运行改进版爬虫"""
        print("🚀 开始上海数据中心改进版爬虫")
        print("🎯 目标：通过真实按钮点击获取所有页面数据")
        print("📄 预期：第1页40个，第2页14个，共54个数据中心")
        print("="*70)
        
        # 1. 测试网络连接
        if not self.test_network_connection():
            print("❌ 网络连接测试失败，无法继续")
            return []
        
        # 2. 初始化WebDriver
        if not self.setup_driver():
            return []
        
        try:
            # 3. 加载页面
            if not self.load_page_with_retry():
                print("❌ 页面加载失败")
                return []
            
            # 4. 分析页面结构
            self.analyze_page_structure()
            
            # 5. 查找页码按钮
            page_buttons = self.find_page_buttons_advanced()
            
            if not page_buttons:
                print("⚠️ 未找到页码按钮，尝试获取第一页数据")
                total_pages = 1
            else:
                total_pages = max(page_buttons.keys())
                print(f"📊 检测到总页数: {total_pages}")
            
            # 6. 逐页爬取数据
            all_datacenters = []
            
            for page_num in range(1, total_pages + 1):
                print(f"\n📄 处理第 {page_num} 页 ({page_num}/{total_pages})")
                
                # 如果不是第一页，需要点击页码按钮
                if page_num > 1:
                    success = self.click_page_button_robust(page_num, page_buttons)
                    if not success:
                        print(f"    无法点击第 {page_num} 页按钮，跳过")
                        continue
                
                # 提取当前页面数据
                page_data = self.extract_data_comprehensive(page_num)
                if page_data:
                    all_datacenters.extend(page_data)
                    print(f"    ✅ 第 {page_num} 页获取 {len(page_data)} 个数据中心")
                    
                    # 显示部分数据
                    for i, dc in enumerate(page_data[:3], 1):
                        print(f"      {i}. {dc['name']} ({dc['latitude']:.6f}, {dc['longitude']:.6f})")
                    if len(page_data) > 3:
                        print(f"      ... 还有 {len(page_data) - 3} 个")
                else:
                    print(f"    ❌ 第 {page_num} 页未获取到数据")
                
                # 保存页面数据
                self.page_data[f'page_{page_num}'] = page_data
                
                time.sleep(2)  # 页面间延迟
            
            # 7. 数据去重和统计
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
            print("\n⏸️ 浏览器将在5秒后关闭...")
            time.sleep(5)
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
        json_file = f"data/shanghai/上海数据中心改进版_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(datacenters, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON文件已保存: {json_file}")
        
        # 保存CSV数据
        csv_file = f"data/shanghai/上海数据中心改进版_{timestamp}.csv"
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            f.write("序号,名称,纬度,经度,位置,来源页,提取方法\n")
            for i, dc in enumerate(datacenters, 1):
                f.write(f"{i},{dc['name']},{dc['latitude']},{dc['longitude']},{dc['location']},第{dc['source_page']}页,{dc['extraction_method']}\n")
        print(f"✅ CSV文件已保存: {csv_file}")
        
        # 生成详细报告
        self.generate_report(datacenters, timestamp)
    
    def generate_report(self, datacenters, timestamp):
        """生成详细报告"""
        report_file = f"data/shanghai/改进版爬取报告_{timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("上海数据中心改进版爬取报告\n")
            f.write("="*60 + "\n\n")
            
            f.write(f"爬取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"爬取方法: Selenium改进版真实按钮点击\n")
            f.write(f"总数据中心: {len(datacenters)} 个\n")
            f.write(f"目标完成度: {len(datacenters)}/54 ({len(datacenters)/54*100:.1f}%)\n\n")
            
            # 详细统计信息
            # ... (类似之前的报告格式)
        
        print(f"✅ 详细报告已保存: {report_file}")

def main():
    """主函数"""
    print("🎯 上海数据中心改进版真实按钮点击爬虫")
    print("🔧 基于成功的测试，应用到真实网站")
    print("📄 预期：第1页40个，第2页14个，共54个数据中心")
    
    crawler = ShanghaiDatacenterCrawler()
    
    try:
        # 运行爬虫
        results = crawler.run_crawler()
        
        if results:
            print(f"\n🎉 爬取完成！")
            print(f"✅ 获取到 {len(results)} 个上海数据中心")
            
            # 保存结果
            crawler.save_results(results)
            
            # 检查是否达到目标
            if len(results) >= 54:
                print(f"\n🎯 目标达成！获取到 {len(results)} 个数据中心 (目标54个)")
            else:
                print(f"\n⚠️ 距离目标还差 {54 - len(results)} 个数据中心")
                print("💡 建议：检查网络连接或页面结构变化")
            
        else:
            print("❌ 未获取到任何数据")
            print("💡 建议：检查网络连接、页面结构或防护措施")
            
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断爬取")
    except Exception as e:
        print(f"❌ 爬取过程中出错: {e}")

if __name__ == "__main__":
    main()
