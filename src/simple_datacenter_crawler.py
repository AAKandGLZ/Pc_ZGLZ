#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版数据中心爬虫
专门针对 gmp-advanced-marker 元素的爬取
"""

import time
import json
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd

class SimpleDataCenterCrawler:
    def __init__(self):
        self.provinces_urls = {
            "四川省": "https://www.datacenters.com/locations/china/sichuan-sheng",
            "云南省": "https://www.datacenters.com/locations/china/yunnan-sheng", 
            "贵州省": "https://www.datacenters.com/locations/china/guizhou-sheng"
        }
        self.results = []
        
    def setup_driver(self):
        """设置Chrome浏览器"""
        chrome_options = Options()
        # 注释掉headless模式，方便调试
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--window-size=1920,1080')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e:
            print(f"浏览器启动失败: {e}")
            return None
    
    def wait_for_map_load(self, driver, timeout=30):
        """等待地图加载完成"""
        print("等待地图加载...")
        time.sleep(10)  # 给足够时间让地图加载
        
        # 尝试等待特定元素出现
        try:
            wait = WebDriverWait(driver, timeout)
            # 等待任何带有position属性的元素
            wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, "[position]"))
            print("地图加载完成")
            return True
        except TimeoutException:
            print("地图加载超时，继续尝试...")
            return False
    
    def extract_markers_info(self, driver):
        """提取所有marker信息"""
        markers_data = []
        
        # 多种选择器策略
        selectors = [
            "gmp-advanced-marker[position]",
            "[position*=',']",
            ".yNHHyP-marker-view[position]",
            "gmp-advanced-marker"
        ]
        
        all_markers = []
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    all_markers.extend(elements)
                    print(f"使用选择器 '{selector}' 找到 {len(elements)} 个元素")
            except Exception as e:
                print(f"选择器 '{selector}' 查找失败: {e}")
        
        # 去重
        unique_markers = []
        seen_positions = set()
        
        for marker in all_markers:
            try:
                position = marker.get_attribute("position")
                if position and position not in seen_positions:
                    unique_markers.append(marker)
                    seen_positions.add(position)
            except:
                continue
        
        print(f"去重后共有 {len(unique_markers)} 个唯一标记")
        
        # 提取每个marker的信息
        for i, marker in enumerate(unique_markers):
            try:
                marker_info = self.extract_single_marker_info(driver, marker, i+1)
                if marker_info:
                    markers_data.append(marker_info)
            except Exception as e:
                print(f"提取第 {i+1} 个标记信息失败: {e}")
                continue
        
        return markers_data
    
    def extract_single_marker_info(self, driver, marker, index):
        """提取单个marker的信息"""
        try:
            # 获取坐标
            position = marker.get_attribute("position")
            if not position:
                return None
            
            coords = position.split(",")
            if len(coords) != 2:
                return None
                
            lat = float(coords[0].strip())
            lng = float(coords[1].strip())
            
            print(f"处理第 {index} 个标记: 坐标 ({lat}, {lng})")
            
            # 尝试点击获取更多信息
            location_name = "未知位置"
            address = ""
            
            try:
                # 滚动到元素可见
                driver.execute_script("arguments[0].scrollIntoView(true);", marker)
                time.sleep(1)
                
                # 点击marker
                marker.click()
                time.sleep(2)
                
                # 查找弹出的信息窗口或侧边栏
                info_selectors = [
                    ".text-sm.text-gray-500",
                    "[class*='text-gray-500']",
                    ".infowindow",
                    ".popup",
                    ".sidebar",
                    ".datacenter-info",
                    "h1", "h2", "h3",
                    ".location-name",
                    ".address"
                ]
                
                for selector in info_selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            text = element.text.strip()
                            if text and len(text) > 3:  # 过滤掉太短的文本
                                if "China" in text or "Sichuan" in text or "Yunnan" in text or "Guizhou" in text:
                                    location_name = text
                                    address = text
                                    break
                    except:
                        continue
                    
                    if location_name != "未知位置":
                        break
                
            except Exception as e:
                print(f"获取标记 {index} 详细信息失败: {e}")
            
            marker_info = {
                'index': index,
                'latitude': lat,
                'longitude': lng,
                'name': location_name,
                'address': address,
                'position_raw': position
            }
            
            print(f"  - 名称: {location_name}")
            return marker_info
            
        except Exception as e:
            print(f"处理标记 {index} 时出错: {e}")
            return None
    
    def crawl_province(self, province_name, url):
        """爬取单个省份"""
        print(f"\n{'='*50}")
        print(f"开始爬取: {province_name}")
        print(f"URL: {url}")
        print(f"{'='*50}")
        
        driver = self.setup_driver()
        if not driver:
            return []
        
        province_results = []
        
        try:
            # 访问页面
            print("正在访问页面...")
            driver.get(url)
            
            # 等待页面加载
            self.wait_for_map_load(driver)
            
            # 提取marker信息
            markers_data = self.extract_markers_info(driver)
            
            # 为每个marker添加省份信息
            for marker in markers_data:
                marker['province'] = province_name
                marker['source_url'] = url
                province_results.append(marker)
            
            print(f"{province_name} 爬取完成，找到 {len(province_results)} 个数据中心")
            
        except Exception as e:
            print(f"爬取 {province_name} 时出错: {e}")
        finally:
            driver.quit()
        
        return province_results
    
    def crawl_all(self):
        """爬取所有省份"""
        print("开始爬取所有省份的数据中心信息...")
        
        for province, url in self.provinces_urls.items():
            try:
                province_data = self.crawl_province(province, url)
                self.results.extend(province_data)
                
                # 省份间休息
                time.sleep(3)
                
            except Exception as e:
                print(f"爬取 {province} 出错: {e}")
                continue
        
        print(f"\n总计爬取完成，共找到 {len(self.results)} 个数据中心")
        return self.results
    
    def save_results(self):
        """保存结果"""
        if not self.results:
            print("没有数据可保存")
            return
        
        # 保存为CSV
        csv_file = "e:\\空间统计分析\\爬虫\\datacenter_results.csv"
        df = pd.DataFrame(self.results)
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"CSV文件保存至: {csv_file}")
        
        # 保存为JSON
        json_file = "e:\\空间统计分析\\爬虫\\datacenter_results.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"JSON文件保存至: {json_file}")
        
        # 打印统计信息
        print(f"\n统计信息:")
        print(f"总数据中心: {len(self.results)}")
        for province in self.provinces_urls.keys():
            count = len([r for r in self.results if r['province'] == province])
            print(f"{province}: {count} 个")
    
    def print_results(self):
        """打印结果"""
        if not self.results:
            print("没有找到任何结果")
            return
        
        print(f"\n{'='*60}")
        print(f"爬取结果 (共 {len(self.results)} 个数据中心)")
        print(f"{'='*60}")
        
        for result in self.results:
            print(f"省份: {result['province']}")
            print(f"坐标: ({result['latitude']}, {result['longitude']})")
            print(f"名称: {result['name']}")
            print(f"地址: {result['address']}")
            print(f"原始位置: {result['position_raw']}")
            print("-" * 40)

def main():
    """主函数"""
    print("简化版数据中心爬虫启动")
    print("目标: 四川省、云南省、贵州省的数据中心")
    
    crawler = SimpleDataCenterCrawler()
    
    try:
        # 执行爬取
        results = crawler.crawl_all()
        
        if results:
            # 显示结果
            crawler.print_results()
            
            # 保存结果
            crawler.save_results()
            
            print(f"\n任务完成！成功获取 {len(results)} 个数据中心信息")
        else:
            print("未获取到任何数据")
            
    except KeyboardInterrupt:
        print("\n用户中断任务")
    except Exception as e:
        print(f"执行过程中出错: {e}")

if __name__ == "__main__":
    main()
