#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据中心爬虫
爬取 https://www.datacenters.com 网站上四川省、云南省、贵州省的数据中心信息
"""

import requests
import json
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import csv
import pandas as pd

class DataCenterCrawler:
    def __init__(self):
        self.base_url = "https://www.datacenters.com"
        self.provinces = {
            "四川省": "https://www.datacenters.com/locations/china/sichuan-sheng",
            "云南省": "https://www.datacenters.com/locations/china/yunnan-sheng", 
            "贵州省": "https://www.datacenters.com/locations/china/guizhou-sheng"
        }
        self.data_centers = []
        
    def setup_driver(self):
        """设置Chrome浏览器驱动"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 无头模式
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e:
            print(f"Chrome驱动初始化失败: {e}")
            print("请确保已安装Chrome浏览器和对应版本的ChromeDriver")
            return None
    
    def extract_coordinates_from_marker(self, marker_element):
        """从marker元素中提取坐标"""
        try:
            # 从position属性中提取坐标
            position = marker_element.get_attribute("position")
            if position:
                coords = position.split(",")
                if len(coords) == 2:
                    lat = float(coords[0].strip())
                    lng = float(coords[1].strip())
                    return lat, lng
        except Exception as e:
            print(f"坐标提取失败: {e}")
        
        return None, None
    
    def extract_location_name(self, driver, marker_element):
        """提取位置名称"""
        try:
            # 尝试点击marker来获取详细信息
            marker_element.click()
            time.sleep(2)
            
            # 查找包含地址信息的元素
            address_selectors = [
                ".text-sm.text-gray-500",
                "[class*='text-gray-500']",
                ".location-name",
                ".address",
                ".datacenter-info"
            ]
            
            for selector in address_selectors:
                try:
                    address_element = driver.find_element(By.CSS_SELECTOR, selector)
                    if address_element and address_element.text.strip():
                        return address_element.text.strip()
                except NoSuchElementException:
                    continue
            
            # 如果找不到具体地址，尝试从页面标题或其他元素获取
            try:
                title_element = driver.find_element(By.TAG_NAME, "h1")
                if title_element:
                    return title_element.text.strip()
            except NoSuchElementException:
                pass
                
        except Exception as e:
            print(f"位置名称提取失败: {e}")
        
        return "未知位置"
    
    def crawl_province(self, province_name, url):
        """爬取指定省份的数据中心信息"""
        print(f"开始爬取 {province_name} 的数据中心信息...")
        
        driver = self.setup_driver()
        if not driver:
            return []
        
        province_data = []
        
        try:
            # 访问页面
            driver.get(url)
            
            # 等待页面加载
            wait = WebDriverWait(driver, 30)
            
            # 等待地图加载完成
            print("等待地图加载...")
            time.sleep(10)
            
            # 查找所有的marker元素
            marker_selectors = [
                "gmp-advanced-marker",
                "[gmp-advanced-marker]",
                ".yNHHyP-marker-view",
                "[role='button'][position]"
            ]
            
            markers = []
            for selector in marker_selectors:
                try:
                    found_markers = driver.find_elements(By.CSS_SELECTOR, selector)
                    if found_markers:
                        markers.extend(found_markers)
                        print(f"找到 {len(found_markers)} 个标记 (使用选择器: {selector})")
                except Exception as e:
                    print(f"选择器 {selector} 查找失败: {e}")
            
            if not markers:
                print(f"未找到任何地图标记，尝试其他方法...")
                # 尝试通过JavaScript获取地图数据
                try:
                    # 执行JavaScript来获取可能的地图数据
                    script = """
                    var markers = [];
                    var elements = document.querySelectorAll('[position]');
                    for (var i = 0; i < elements.length; i++) {
                        var pos = elements[i].getAttribute('position');
                        if (pos && pos.includes(',')) {
                            markers.push({
                                position: pos,
                                element: elements[i]
                            });
                        }
                    }
                    return markers;
                    """
                    js_markers = driver.execute_script(script)
                    print(f"通过JavaScript找到 {len(js_markers)} 个标记")
                    
                    for js_marker in js_markers:
                        try:
                            position = js_marker['position']
                            coords = position.split(",")
                            if len(coords) == 2:
                                lat = float(coords[0].strip())
                                lng = float(coords[1].strip())
                                
                                data_center = {
                                    'province': province_name,
                                    'latitude': lat,
                                    'longitude': lng,
                                    'name': f"{province_name}数据中心",
                                    'address': "地址获取中...",
                                    'url': url
                                }
                                province_data.append(data_center)
                                print(f"找到数据中心: {lat}, {lng}")
                        except Exception as e:
                            print(f"JavaScript标记处理失败: {e}")
                            
                except Exception as e:
                    print(f"JavaScript执行失败: {e}")
            
            else:
                print(f"在 {province_name} 找到 {len(markers)} 个数据中心标记")
                
                for i, marker in enumerate(markers):
                    try:
                        print(f"处理第 {i+1} 个标记...")
                        
                        # 提取坐标
                        lat, lng = self.extract_coordinates_from_marker(marker)
                        
                        if lat is not None and lng is not None:
                            # 提取位置名称
                            location_name = self.extract_location_name(driver, marker)
                            
                            data_center = {
                                'province': province_name,
                                'latitude': lat,
                                'longitude': lng,
                                'name': location_name,
                                'address': location_name,
                                'url': url
                            }
                            
                            province_data.append(data_center)
                            print(f"成功提取数据中心: {location_name} ({lat}, {lng})")
                        else:
                            print(f"第 {i+1} 个标记坐标提取失败")
                            
                        time.sleep(1)  # 避免操作过快
                        
                    except Exception as e:
                        print(f"处理第 {i+1} 个标记时出错: {e}")
                        continue
            
        except TimeoutException:
            print(f"页面加载超时: {url}")
        except Exception as e:
            print(f"爬取 {province_name} 时出错: {e}")
        finally:
            driver.quit()
        
        print(f"{province_name} 爬取完成，共找到 {len(province_data)} 个数据中心")
        return province_data
    
    def crawl_all_provinces(self):
        """爬取所有省份的数据中心信息"""
        print("开始爬取所有省份的数据中心信息...")
        
        for province, url in self.provinces.items():
            try:
                province_data = self.crawl_province(province, url)
                self.data_centers.extend(province_data)
                
                # 每个省份之间稍作休息
                time.sleep(5)
                
            except Exception as e:
                print(f"爬取 {province} 失败: {e}")
                continue
        
        print(f"所有省份爬取完成，共找到 {len(self.data_centers)} 个数据中心")
        return self.data_centers
    
    def save_to_csv(self, filename="data_centers.csv"):
        """保存数据到CSV文件"""
        if not self.data_centers:
            print("没有数据可保存")
            return
        
        filepath = f"e:\\空间统计分析\\爬虫\\{filename}"
        
        try:
            df = pd.DataFrame(self.data_centers)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            print(f"数据已保存到: {filepath}")
            
            # 显示统计信息
            print("\n数据统计:")
            print(f"总数据中心数量: {len(self.data_centers)}")
            print("\n各省份分布:")
            province_counts = df['province'].value_counts()
            for province, count in province_counts.items():
                print(f"  {province}: {count} 个")
                
        except Exception as e:
            print(f"保存CSV文件失败: {e}")
    
    def save_to_json(self, filename="data_centers.json"):
        """保存数据到JSON文件"""
        if not self.data_centers:
            print("没有数据可保存")
            return
        
        filepath = f"e:\\空间统计分析\\爬虫\\{filename}"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.data_centers, f, ensure_ascii=False, indent=2)
            print(f"数据已保存到: {filepath}")
        except Exception as e:
            print(f"保存JSON文件失败: {e}")
    
    def print_results(self):
        """打印爬取结果"""
        if not self.data_centers:
            print("没有找到任何数据中心信息")
            return
        
        print(f"\n爬取结果总览:")
        print(f"总共找到 {len(self.data_centers)} 个数据中心")
        print("-" * 80)
        
        for i, dc in enumerate(self.data_centers, 1):
            print(f"{i}. {dc['province']} - {dc['name']}")
            print(f"   坐标: ({dc['latitude']}, {dc['longitude']})")
            print(f"   地址: {dc['address']}")
            print(f"   来源: {dc['url']}")
            print("-" * 40)

def main():
    """主函数"""
    print("数据中心爬虫启动...")
    print("目标省份: 四川省、云南省、贵州省")
    print("-" * 50)
    
    crawler = DataCenterCrawler()
    
    try:
        # 爬取所有省份数据
        data_centers = crawler.crawl_all_provinces()
        
        if data_centers:
            # 打印结果
            crawler.print_results()
            
            # 保存数据
            crawler.save_to_csv()
            crawler.save_to_json()
            
            print(f"\n爬取任务完成！共获取 {len(data_centers)} 个数据中心信息")
        else:
            print("未能获取到任何数据中心信息")
            
    except KeyboardInterrupt:
        print("\n用户中断爬取任务")
    except Exception as e:
        print(f"爬取过程中出现错误: {e}")

if __name__ == "__main__":
    main()
