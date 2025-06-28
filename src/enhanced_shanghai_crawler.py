#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版上海市数据中心爬虫
支持地图缩放、翻页和JavaScript渲染，获取完整的数据中心信息
"""

import requests
import re
import json
import pandas as pd
import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedShanghaiDataCenterCrawler:
    def __init__(self):
        # 上海市的主要URL
        self.main_url = "https://www.datacenters.com/locations/china/shanghai/shanghai"
        
        # 上海市行政区域坐标范围（更精确的边界）
        self.shanghai_bounds = {
            'lat_min': 30.6,    # 最南端（奉贤区南部）
            'lat_max': 31.9,    # 最北端（崇明岛北部）
            'lng_min': 120.8,   # 最西端（青浦区西部）
            'lng_max': 122.2    # 最东端（崇明岛东部）
        }
        
        # 上海市各区的中心坐标（用于验证）
        self.shanghai_districts = {
            '黄浦区': (31.2304, 121.4737),
            '徐汇区': (31.1880, 121.4370),
            '长宁区': (31.2200, 121.4252),
            '静安区': (31.2290, 121.4480),
            '普陀区': (31.2500, 121.3960),
            '虹口区': (31.2650, 121.5050),
            '杨浦区': (31.2590, 121.5220),
            '浦东新区': (31.2450, 121.5670),
            '闵行区': (31.1120, 121.3810),
            '宝山区': (31.4040, 121.4890),
            '嘉定区': (31.3760, 121.2650),
            '金山区': (30.7410, 121.3420),
            '松江区': (31.0300, 121.2230),
            '青浦区': (31.1510, 121.1240),
            '奉贤区': (30.9180, 121.4740),
            '崇明区': (31.6230, 121.3970)
        }
        
        self.all_results = []
        self.unique_coordinates = set()
        self.driver = None
        
        # 创建输出目录
        self.create_output_directories()
    
    def create_output_directories(self):
        """创建输出目录结构"""
        directories = [
            "data/shanghai",
            "reports/shanghai", 
            "html_sources/shanghai"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def setup_driver(self):
        """设置Chrome WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 无头模式
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # 禁用图片加载以提高速度
            prefs = {"profile.managed_default_content_settings.images": 2}
            chrome_options.add_experimental_option("prefs", prefs)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            logger.info("✅ Chrome WebDriver 初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ WebDriver 初始化失败: {e}")
            # 回退到requests方式
            return False
    
    def is_in_shanghai(self, lat, lng):
        """检查坐标是否在上海市范围内"""
        return (self.shanghai_bounds['lat_min'] <= lat <= self.shanghai_bounds['lat_max'] and
                self.shanghai_bounds['lng_min'] <= lng <= self.shanghai_bounds['lng_max'])
    
    def get_district_by_coordinates(self, lat, lng):
        """根据坐标推断所属区域"""
        min_distance = float('inf')
        closest_district = "上海市"
        
        for district, (d_lat, d_lng) in self.shanghai_districts.items():
            distance = ((lat - d_lat) ** 2 + (lng - d_lng) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                closest_district = district
        
        # 如果距离太远，说明可能不在上海市内
        if min_distance > 0.5:  # 约55公里
            return None
        
        return closest_district
    
    def extract_data_with_selenium(self):
        """使用Selenium提取数据"""
        try:
            logger.info(f"🌐 正在访问: {self.main_url}")
            self.driver.get(self.main_url)
            
            # 等待页面加载
            time.sleep(5)
            
            # 尝试找到地图容器
            try:
                map_container = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "map-container"))
                )
                logger.info("✅ 找到地图容器")
            except TimeoutException:
                try:
                    map_container = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.ID, "map"))
                    )
                    logger.info("✅ 找到地图元素")
                except TimeoutException:
                    logger.warning("⚠️ 未找到地图容器，继续使用页面源码")
            
            # 尝试多种缩放级别
            zoom_levels = [10, 11, 12, 13, 14, 15]
            all_data = []
            
            for zoom in zoom_levels:
                logger.info(f"🔍 尝试缩放级别: {zoom}")
                
                # 尝试设置地图缩放（如果支持）
                try:
                    self.driver.execute_script(f"""
                        if (window.map && window.map.setZoom) {{
                            window.map.setZoom({zoom});
                        }}
                    """)
                    time.sleep(3)
                except:
                    pass
                
                # 提取当前页面数据
                page_data = self.extract_data_from_page_source()
                if page_data:
                    all_data.extend(page_data)
                    logger.info(f"  📊 缩放级别 {zoom}: 找到 {len(page_data)} 个数据中心")
                
                # 尝试点击更多按钮或加载更多
                try:
                    load_more_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Load More') or contains(text(), 'Show More') or contains(text(), '加载更多') or contains(text(), '显示更多')]")
                    for button in load_more_buttons:
                        if button.is_displayed() and button.is_enabled():
                            self.driver.execute_script("arguments[0].click();", button)
                            logger.info("🔄 点击了加载更多按钮")
                            time.sleep(3)
                            
                            # 提取新加载的数据
                            new_data = self.extract_data_from_page_source()
                            if new_data:
                                all_data.extend(new_data)
                except:
                    pass
                
                # 尝试滚动页面触发懒加载
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)
            
            # 尝试翻页
            page_num = 1
            while page_num <= 10:  # 最多尝试10页
                try:
                    # 查找下一页按钮
                    next_buttons = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Next') or contains(text(), '下一页') or contains(@class, 'next')] | //button[contains(text(), 'Next') or contains(text(), '下一页')]")
                    
                    clicked = False
                    for button in next_buttons:
                        if button.is_displayed() and button.is_enabled():
                            self.driver.execute_script("arguments[0].click();", button)
                            logger.info(f"📄 跳转到第 {page_num + 1} 页")
                            time.sleep(5)
                            
                            # 提取新页面数据
                            page_data = self.extract_data_from_page_source()
                            if page_data:
                                all_data.extend(page_data)
                                logger.info(f"  📊 第 {page_num + 1} 页: 找到 {len(page_data)} 个数据中心")
                            clicked = True
                            break
                    
                    if not clicked:
                        break
                    
                    page_num += 1
                    
                except Exception as e:
                    logger.info(f"📄 翻页结束: {e}")
                    break
            
            # 去重并过滤
            filtered_data = []
            seen_coords = set()
            
            for data_center in all_data:
                coord_key = (round(data_center['latitude'], 6), round(data_center['longitude'], 6))
                if coord_key not in seen_coords:
                    seen_coords.add(coord_key)
                    filtered_data.append(data_center)
            
            logger.info(f"🎯 总计找到 {len(all_data)} 个数据中心，去重后 {len(filtered_data)} 个")
            return filtered_data
            
        except Exception as e:
            logger.error(f"❌ Selenium提取数据失败: {e}")
            return []
    
    def extract_data_from_page_source(self):
        """从当前页面源码提取数据"""
        try:
            page_source = self.driver.page_source
            return self.extract_data_from_content(page_source)
        except:
            return []
    
    def extract_data_from_content(self, content):
        """从内容中提取数据中心信息"""
        found_data = []
        
        try:
            # 多种坐标提取模式
            coordinate_patterns = [
                # JSON格式
                r'"lat":\s*([\d\.\-]+).*?"lng":\s*([\d\.\-]+)',
                r'"latitude":\s*([\d\.\-]+).*?"longitude":\s*([\d\.\-]+)',
                r'"y":\s*([\d\.\-]+).*?"x":\s*([\d\.\-]+)',
                
                # JavaScript格式
                r'lat:\s*([\d\.\-]+).*?lng:\s*([\d\.\-]+)',
                r'latitude:\s*([\d\.\-]+).*?longitude:\s*([\d\.\-]+)',
                
                # 数组格式
                r'\[([\d\.\-]+),\s*([\d\.\-]+)\]',
                
                # 其他格式
                r'position:\s*\{\s*lat:\s*([\d\.\-]+).*?lng:\s*([\d\.\-]+)',
            ]
            
            # 名称提取模式
            name_patterns = [
                r'"name":\s*"([^"]*(?:Data Center|IDC|数据中心|机房|云计算|Cloud|DC)[^"]*)"',
                r'"title":\s*"([^"]*(?:Data Center|IDC|数据中心|机房|云计算|Cloud|DC)[^"]*)"',
                r'"facility_name":\s*"([^"]*)"',
                r'<h[1-6][^>]*>([^<]*(?:Data Center|IDC|数据中心|机房|云计算|Cloud|DC)[^<]*)</h[1-6]>',
                r'"name":\s*"([^"]*(?:上海|Shanghai|SH)[^"]*)"',
                r'data-name="([^"]*)"',
                r'title="([^"]*(?:Data Center|IDC|数据中心)[^"]*)"',
            ]
            
            # 收集所有坐标
            all_coordinates = []
            for pattern in coordinate_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    try:
                        if len(match) == 2:
                            lat, lng = float(match[0]), float(match[1])
                            # 验证坐标合理性
                            if 20 <= lat <= 50 and 100 <= lng <= 130:
                                all_coordinates.append((lat, lng))
                    except:
                        continue
            
            # 收集所有名称
            all_names = []
            for pattern in name_patterns:
                names = re.findall(pattern, content, re.IGNORECASE)
                all_names.extend([name.strip() for name in names if name.strip()])
            
            # 去重坐标
            unique_coords = list(set(all_coordinates))
            logger.info(f"  📍 提取到 {len(unique_coords)} 个唯一坐标")
            
            # 过滤上海市范围内的坐标
            shanghai_coords = []
            filtered_out = 0
            
            for lat, lng in unique_coords:
                if self.is_in_shanghai(lat, lng):
                    district = self.get_district_by_coordinates(lat, lng)
                    if district:  # 确保能匹配到区域
                        shanghai_coords.append((lat, lng, district))
                    else:
                        filtered_out += 1
                else:
                    filtered_out += 1
            
            logger.info(f"  ✅ 上海市内坐标: {len(shanghai_coords)} 个")
            logger.info(f"  ❌ 过滤掉周边地区: {filtered_out} 个")
            
            # 创建数据中心记录
            for i, (lat, lng, district) in enumerate(shanghai_coords):
                # 检查是否重复
                coord_key = (round(lat, 6), round(lng, 6))
                if coord_key in self.unique_coordinates:
                    continue
                
                self.unique_coordinates.add(coord_key)
                
                # 选择名称
                if i < len(all_names):
                    name = all_names[i]
                else:
                    name = f"{district}数据中心{len(found_data)+1}"
                
                data_center = {
                    'province': '上海市',
                    'district': district,
                    'latitude': lat,
                    'longitude': lng,
                    'name': name,
                    'source': 'enhanced_crawler',
                    'coordinates': f"{lat},{lng}",
                    'index': len(self.all_results) + len(found_data) + 1,
                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                found_data.append(data_center)
            
            return found_data
            
        except Exception as e:
            logger.error(f"❌ 数据提取错误: {e}")
            return []
    
    def crawl_with_requests_fallback(self):
        """使用requests作为备用方案"""
        logger.info("🔄 使用requests备用方案")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        
        try:
            response = requests.get(self.main_url, headers=headers, timeout=30)
            if response.status_code == 200:
                return self.extract_data_from_content(response.text)
        except Exception as e:
            logger.error(f"❌ requests备用方案失败: {e}")
        
        return []
    
    def crawl_all_data(self):
        """爬取所有数据"""
        logger.info("🚀 启动增强版上海市数据中心爬虫")
        logger.info("🎯 目标：获取完整的上海市数据中心信息（80+个）")
        logger.info("="*70)
        
        all_data = []
        
        # 尝试使用Selenium
        if self.setup_driver():
            try:
                selenium_data = self.extract_data_with_selenium()
                all_data.extend(selenium_data)
                logger.info(f"✅ Selenium方式获取: {len(selenium_data)} 个数据中心")
            except Exception as e:
                logger.error(f"❌ Selenium方式失败: {e}")
            finally:
                if self.driver:
                    self.driver.quit()
        
        # 如果Selenium数据不够，使用requests备用
        if len(all_data) < 50:  # 期望至少50个
            logger.info("📊 数据量不足，启用requests备用方案")
            requests_data = self.crawl_with_requests_fallback()
            
            # 合并数据并去重
            seen_coords = set()
            for dc in all_data:
                seen_coords.add((round(dc['latitude'], 6), round(dc['longitude'], 6)))
            
            for dc in requests_data:
                coord_key = (round(dc['latitude'], 6), round(dc['longitude'], 6))
                if coord_key not in seen_coords:
                    all_data.append(dc)
                    seen_coords.add(coord_key)
        
        self.all_results = all_data
        logger.info(f"🎉 最终获取: {len(self.all_results)} 个上海市数据中心")
        return self.all_results
    
    def save_results(self):
        """保存结果"""
        if not self.all_results:
            logger.error("❌ 没有数据需要保存")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 统计信息
        district_stats = {}
        for result in self.all_results:
            district = result['district']
            district_stats[district] = district_stats.get(district, 0) + 1
        
        logger.info(f"\n📊 数据统计:")
        total = sum(district_stats.values())
        for district, count in district_stats.items():
            logger.info(f"  {district}: {count} 个数据中心")
        logger.info(f"  📍 总计: {total} 个数据中心")
        
        # 保存CSV
        csv_file = f"data/shanghai/上海市数据中心坐标_enhanced_{timestamp}.csv"
        try:
            df = pd.DataFrame(self.all_results)
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            logger.info(f"✅ CSV文件已保存: {csv_file}")
        except Exception as e:
            logger.error(f"❌ 保存CSV失败: {e}")
        
        # 保存JSON
        json_file = f"data/shanghai/上海市数据中心坐标_enhanced_{timestamp}.json"
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_results, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ JSON文件已保存: {json_file}")
        except Exception as e:
            logger.error(f"❌ 保存JSON失败: {e}")
        
        # 生成详细报告
        self.generate_enhanced_report(timestamp)
    
    def generate_enhanced_report(self, timestamp):
        """生成增强版报告"""
        report_file = f"reports/shanghai/上海市数据中心分布报告_enhanced_{timestamp}.txt"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("上海市数据中心分布分析报告（增强版）\n")
                f.write("=" * 60 + "\n\n")
                
                f.write(f"爬取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"爬取方式: Selenium + requests 双重保障\n")
                f.write(f"总数据中心数量: {len(self.all_results)}\n")
                f.write(f"预期目标: 80+ 个数据中心\n")
                f.write(f"完成度: {len(self.all_results)/80*100:.1f}%\n\n")
                
                # 区域分布统计
                district_data = {}
                for result in self.all_results:
                    district = result['district']
                    if district not in district_data:
                        district_data[district] = []
                    district_data[district].append(result)
                
                f.write(f"区域分布统计:\n")
                f.write("-" * 30 + "\n")
                for district, data in district_data.items():
                    percentage = len(data) / len(self.all_results) * 100
                    f.write(f"{district}: {len(data)} 个 ({percentage:.1f}%)\n")
                
                f.write(f"\n详细列表:\n")
                f.write("-" * 30 + "\n")
                
                for district, data in district_data.items():
                    f.write(f"\n{district} ({len(data)} 个):\n")
                    for i, dc in enumerate(data, 1):
                        f.write(f"  {i:2d}. {dc['name']}\n")
                        f.write(f"      坐标: ({dc['latitude']:.6f}, {dc['longitude']:.6f})\n")
                        f.write(f"      爬取时间: {dc['crawl_time']}\n\n")
                
                # 技术说明
                f.write(f"技术改进说明:\n")
                f.write("-" * 30 + "\n")
                f.write(f"1. 使用Selenium处理JavaScript渲染\n")
                f.write(f"2. 支持多种地图缩放级别\n")
                f.write(f"3. 自动翻页获取更多数据\n")
                f.write(f"4. 智能点击'加载更多'按钮\n")
                f.write(f"5. 滚动页面触发懒加载\n")
                f.write(f"6. requests备用方案保障\n")
                f.write(f"7. 精确的上海市行政区域过滤\n")
                f.write(f"8. 坐标去重和数据验证\n")
            
            logger.info(f"✅ 增强版报告已保存: {report_file}")
            
        except Exception as e:
            logger.error(f"❌ 生成报告失败: {e}")
    
    def display_results(self):
        """显示结果"""
        if not self.all_results:
            logger.error("❌ 没有找到任何数据")
            return
        
        print(f"\n{'='*80}")
        print(f"🎯 上海市数据中心爬取结果（增强版）")
        print(f"{'='*80}")
        
        # 按区域分组显示
        district_data = {}
        for result in self.all_results:
            district = result['district']
            if district not in district_data:
                district_data[district] = []
            district_data[district].append(result)
        
        for district, data in district_data.items():
            print(f"\n📍 {district} ({len(data)} 个数据中心):")
            print("-" * 50)
            for i, dc in enumerate(data, 1):
                print(f"{i:2d}. {dc['name']}")
                print(f"    🗺️  坐标: ({dc['latitude']:.6f}, {dc['longitude']:.6f})")
                print(f"    ⏰ 时间: {dc['crawl_time']}")
                print()

def main():
    """主函数"""
    print("🚀 增强版上海市数据中心爬虫启动")
    print("🎯 目标：获取完整的上海市数据中心信息（80+个）")
    print("🔧 技术：Selenium + 地图缩放 + 翻页 + requests备用")
    
    crawler = EnhancedShanghaiDataCenterCrawler()
    
    try:
        # 开始爬取
        results = crawler.crawl_all_data()
        
        if results:
            # 显示结果
            crawler.display_results()
            
            # 保存数据
            crawler.save_results()
            
            print(f"\n🎉 任务完成！")
            print(f"✅ 成功获取 {len(results)} 个上海市数据中心")
            if len(results) >= 80:
                print(f"🎯 达到预期目标（80+个）")
            else:
                print(f"⚠️ 未达到预期目标，可能需要进一步优化")
            
            print(f"✅ 数据已保存到 data/shanghai/ 目录")
            print(f"✅ 报告已生成到 reports/shanghai/ 目录")
            
        else:
            print("❌ 未获取到任何数据")
            print("💡 建议检查网络连接或目标网站结构变化")
            
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断任务")
    except Exception as e:
        logger.error(f"❌ 执行过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
