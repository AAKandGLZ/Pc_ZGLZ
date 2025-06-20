#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动管理ChromeDriver的数据中心爬虫
使用webdriver-manager自动下载和管理ChromeDriver
"""

import time
import json
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

class AutoDataCenterCrawler:
    def __init__(self):
        self.provinces_urls = {
            "四川省": "https://www.datacenters.com/locations/china/sichuan-sheng",
            "云南省": "https://www.datacenters.com/locations/china/yunnan-sheng", 
            "贵州省": "https://www.datacenters.com/locations/china/guizhou-sheng"
        }
        self.results = []
        
    def setup_driver(self):
        """自动设置Chrome浏览器和驱动"""
        try:
            print("正在自动下载和配置ChromeDriver...")
            
            chrome_options = Options()
            # 可以选择是否使用无头模式
            # chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # 使用webdriver-manager自动管理ChromeDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            print("ChromeDriver配置成功！")
            return driver
            
        except Exception as e:
            print(f"浏览器启动失败: {e}")
            print("请确保已安装Chrome浏览器")
            return None
    
    def wait_for_page_load(self, driver, timeout=30):
        """等待页面和地图加载完成"""
        print("等待页面加载...")
        
        try:
            # 等待页面基本加载完成
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # 额外等待时间让地图渲染
            time.sleep(15)
            
            # 尝试等待地图相关元素
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[position]"))
                )
                print("检测到地图标记元素")
            except TimeoutException:
                print("未检测到地图标记，但继续执行...")
            
            return True
            
        except TimeoutException:
            print("页面加载超时")
            return False
    
    def find_all_markers(self, driver):
        """查找所有地图标记"""
        print("正在查找地图标记...")
        
        # 多种选择器策略
        selectors = [
            "gmp-advanced-marker[position]",
            "[position*=',']",
            "gmp-advanced-marker",
            "[tabindex='-1'][position]",
            ".yNHHyP-marker-view",
            "[role='button'][position]"
        ]
        
        all_elements = []
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"选择器 '{selector}' 找到 {len(elements)} 个元素")
                    all_elements.extend(elements)
            except Exception as e:
                print(f"选择器 '{selector}' 执行失败: {e}")
        
        # 过滤出有position属性的元素
        valid_markers = []
        seen_positions = set()
        
        for element in all_elements:
            try:
                position = element.get_attribute("position")
                if position and "," in position and position not in seen_positions:
                    valid_markers.append(element)
                    seen_positions.add(position)
            except:
                continue
        
        print(f"找到 {len(valid_markers)} 个有效的地图标记")
        return valid_markers
    
    def extract_marker_data(self, driver, marker, index):
        """提取单个标记的数据"""
        try:
            position = marker.get_attribute("position")
            if not position or "," not in position:
                return None
            
            # 解析坐标
            coords = position.split(",")
            lat = float(coords[0].strip())
            lng = float(coords[1].strip())
            
            print(f"处理标记 {index}: 坐标 ({lat}, {lng})")
            
            # 尝试获取更多信息
            name = "未知位置"
            address = ""
            
            try:
                # 滚动到元素可见区域
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", marker)
                time.sleep(1)
                
                # 尝试点击获取信息
                driver.execute_script("arguments[0].click();", marker)
                time.sleep(3)
                
                # 查找信息窗口或弹出内容
                info_selectors = [
                    ".text-sm.text-gray-500",
                    "[class*='text-gray-500']",
                    ".infowindow",
                    ".popup-content",
                    ".location-info",
                    ".datacenter-name",
                    "h1, h2, h3",
                    ".address",
                    "[class*='address']"
                ]
                
                for selector in info_selectors:
                    try:
                        info_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in info_elements:
                            text = elem.text.strip()
                            if text and len(text) > 5:
                                # 判断是否包含中国地址信息
                                if any(keyword in text for keyword in ["China", "Sichuan", "Yunnan", "Guizhou", "四川", "云南", "贵州"]):
                                    name = text
                                    address = text
                                    print(f"  找到位置信息: {text}")
                                    break
                    except:
                        continue
                    
                    if name != "未知位置":
                        break
                
            except Exception as e:
                print(f"  获取详细信息失败: {e}")
            
            # 构建数据
            marker_data = {
                'index': index,
                'latitude': lat,
                'longitude': lng,
                'name': name,
                'address': address,
                'position_raw': position
            }
            
            return marker_data
            
        except Exception as e:
            print(f"处理标记 {index} 时出错: {e}")
            return None
    
    def crawl_province(self, province_name, url):
        """爬取单个省份的数据"""
        print(f"\n{'='*60}")
        print(f"开始爬取: {province_name}")
        print(f"URL: {url}")
        print(f"{'='*60}")
        
        driver = self.setup_driver()
        if not driver:
            print(f"无法启动浏览器，跳过 {province_name}")
            return []
        
        province_data = []
        
        try:
            # 访问页面
            print("正在访问页面...")
            driver.get(url)
            
            # 等待页面加载
            if not self.wait_for_page_load(driver):
                print("页面加载失败")
                return []
            
            # 查找标记
            markers = self.find_all_markers(driver)
            
            if not markers:
                print(f"在 {province_name} 未找到任何地图标记")
                return []
            
            # 提取每个标记的数据
            print(f"开始提取 {len(markers)} 个标记的数据...")
            
            for i, marker in enumerate(markers, 1):
                marker_data = self.extract_marker_data(driver, marker, i)
                if marker_data:
                    marker_data['province'] = province_name
                    marker_data['source_url'] = url
                    province_data.append(marker_data)
                
                # 标记间稍作休息
                time.sleep(1)
            
            print(f"{province_name} 爬取完成，共获取 {len(province_data)} 个数据中心")
            
        except Exception as e:
            print(f"爬取 {province_name} 时发生错误: {e}")
        finally:
            try:
                driver.quit()
            except:
                pass
        
        return province_data
    
    def run_crawler(self):
        """运行完整的爬取流程"""
        print("=" * 80)
        print("数据中心爬虫启动")
        print("目标省份: 四川省、云南省、贵州省")
        print("=" * 80)
        
        for province, url in self.provinces_urls.items():
            try:
                province_data = self.crawl_province(province, url)
                self.results.extend(province_data)
                
                # 省份间休息
                if province != list(self.provinces_urls.keys())[-1]:  # 不是最后一个省份
                    print("休息5秒后继续...")
                    time.sleep(5)
                
            except Exception as e:
                print(f"处理 {province} 时出错: {e}")
                continue
        
        return self.results
    
    def save_data(self):
        """保存数据到文件"""
        if not self.results:
            print("没有数据需要保存")
            return
        
        # 保存CSV
        csv_path = "e:\\空间统计分析\\爬虫\\datacenter_final_results.csv"
        try:
            df = pd.DataFrame(self.results)
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"CSV文件已保存: {csv_path}")
        except Exception as e:
            print(f"保存CSV失败: {e}")
        
        # 保存JSON
        json_path = "e:\\空间统计分析\\爬虫\\datacenter_final_results.json"
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            print(f"JSON文件已保存: {json_path}")
        except Exception as e:
            print(f"保存JSON失败: {e}")
    
    def display_summary(self):
        """显示爬取结果摘要"""
        if not self.results:
            print("没有找到任何数据中心")
            return
        
        print(f"\n{'='*80}")
        print(f"爬取结果摘要")
        print(f"{'='*80}")
        print(f"总数据中心数量: {len(self.results)}")
        
        # 按省份统计
        province_stats = {}
        for result in self.results:
            province = result['province']
            province_stats[province] = province_stats.get(province, 0) + 1
        
        print("\n各省份分布:")
        for province, count in province_stats.items():
            print(f"  {province}: {count} 个数据中心")
        
        print(f"\n详细列表:")
        print("-" * 80)
        for i, result in enumerate(self.results, 1):
            print(f"{i:2d}. {result['province']} - {result['name']}")
            print(f"    坐标: ({result['latitude']:.6f}, {result['longitude']:.6f})")
            print(f"    地址: {result['address']}")
            print("-" * 40)

def main():
    """主函数"""
    crawler = AutoDataCenterCrawler()
    
    try:
        # 执行爬取
        results = crawler.run_crawler()
        
        # 显示结果
        crawler.display_summary()
        
        # 保存数据
        crawler.save_data()
        
        if results:
            print(f"\n任务完成！成功爬取 {len(results)} 个数据中心信息")
            print("数据已保存到CSV和JSON文件中")
        else:
            print("\n任务完成，但未获取到任何数据")
            print("可能的原因:")
            print("1. 网络连接问题")
            print("2. 网站结构发生变化")
            print("3. 需要调整等待时间或选择器")
            
    except KeyboardInterrupt:
        print("\n\n用户中断了爬取任务")
    except Exception as e:
        print(f"\n执行过程中发生错误: {e}")

if __name__ == "__main__":
    main()
