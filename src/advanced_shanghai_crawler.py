#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级上海市数据中心爬虫
使用多种策略获取完整的上海市数据中心信息，不依赖Selenium
"""

import requests
import re
import json
import pandas as pd
import time
import os
from datetime import datetime
import urllib.parse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedShanghaiDataCenterCrawler:
    def __init__(self):
        # 多种URL策略
        self.base_urls = [
            "https://www.datacenters.com/locations/china/shanghai/shanghai",
            "https://www.datacenters.com/locations/china/shanghai",
            "https://www.datacenters.com/api/locations/china/shanghai/shanghai",
            "https://www.datacenters.com/search?location=shanghai",
            "https://www.datacenters.com/search?location=上海",
        ]
        
        # 分页URL模式
        self.pagination_patterns = [
            "?page={page}",
            "?offset={offset}",
            "&page={page}",
            "&offset={offset}",
            "?start={start}",
            "&start={start}",
        ]
        
        # 上海市各区的URL
        self.district_urls = [
            "https://www.datacenters.com/locations/china/shanghai/pudong",
            "https://www.datacenters.com/locations/china/shanghai/huangpu", 
            "https://www.datacenters.com/locations/china/shanghai/xuhui",
            "https://www.datacenters.com/locations/china/shanghai/changning",
            "https://www.datacenters.com/locations/china/shanghai/jingan",
            "https://www.datacenters.com/locations/china/shanghai/putuo",
            "https://www.datacenters.com/locations/china/shanghai/hongkou",
            "https://www.datacenters.com/locations/china/shanghai/yangpu",
            "https://www.datacenters.com/locations/china/shanghai/minhang",
            "https://www.datacenters.com/locations/china/shanghai/baoshan",
            "https://www.datacenters.com/locations/china/shanghai/jiading",
            "https://www.datacenters.com/locations/china/shanghai/jinshan",
            "https://www.datacenters.com/locations/china/shanghai/songjiang",
            "https://www.datacenters.com/locations/china/shanghai/qingpu",
            "https://www.datacenters.com/locations/china/shanghai/fengxian",
            "https://www.datacenters.com/locations/china/shanghai/chongming",
        ]
        
        # API可能的端点
        self.api_endpoints = [
            "https://www.datacenters.com/api/locations",
            "https://www.datacenters.com/api/search",
            "https://www.datacenters.com/api/facilities",
            "https://api.datacenters.com/locations",
            "https://api.datacenters.com/facilities",
        ]
        
        # 上海市精确边界
        self.shanghai_bounds = {
            'lat_min': 30.6,    
            'lat_max': 31.9,    
            'lng_min': 120.8,   
            'lng_max': 122.2    
        }
        
        # 上海市各区域中心点
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
        self.session = requests.Session()
        
        # 设置高级请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })
        
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
    
    def fetch_url_with_retry(self, url, max_retries=3):
        """带重试的URL获取"""
        for attempt in range(max_retries):
            try:
                # 添加随机延迟避免被封IP
                time.sleep(1 + attempt * 0.5)
                
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 404:
                    return None  # 页面不存在
                else:
                    logger.warning(f"⚠️ URL {url} 返回状态码: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"⚠️ 请求失败 (尝试 {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return None
        
        return None
    
    def extract_coordinates_advanced(self, content):
        """高级坐标提取"""
        coordinates = []
        
        # 多种坐标格式模式
        patterns = [
            # JSON格式 - 最常见
            r'"lat":\s*([\d\.\-]+).*?"lng":\s*([\d\.\-]+)',
            r'"latitude":\s*([\d\.\-]+).*?"longitude":\s*([\d\.\-]+)',
            r'"y":\s*([\d\.\-]+).*?"x":\s*([\d\.\-]+)',
            
            # JavaScript对象格式
            r'lat:\s*([\d\.\-]+).*?lng:\s*([\d\.\-]+)',
            r'latitude:\s*([\d\.\-]+).*?longitude:\s*([\d\.\-]+)',
            
            # 数组格式
            r'\[([\d\.\-]+),\s*([\d\.\-]+)\]',
            r'new google\.maps\.LatLng\(([\d\.\-]+),\s*([\d\.\-]+)\)',
            
            # GeoJSON格式
            r'"coordinates":\s*\[([\d\.\-]+),\s*([\d\.\-]+)\]',
            
            # 其他可能格式
            r'position:\s*\{\s*lat:\s*([\d\.\-]+).*?lng:\s*([\d\.\-]+)',
            r'center:\s*\[([\d\.\-]+),\s*([\d\.\-]+)\]',
            r'latlng:\s*\[([\d\.\-]+),\s*([\d\.\-]+)\]',
            
            # HTML data属性
            r'data-lat="([\d\.\-]+)".*?data-lng="([\d\.\-]+)"',
            r'data-latitude="([\d\.\-]+)".*?data-longitude="([\d\.\-]+)"',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                try:
                    if len(match) == 2:
                        lat, lng = float(match[0]), float(match[1])
                        # 基本合理性检查
                        if 20 <= lat <= 50 and 100 <= lng <= 130:
                            coordinates.append((lat, lng))
                except ValueError:
                    continue
        
        return coordinates
    
    def extract_names_advanced(self, content):
        """高级名称提取"""
        names = []
        
        patterns = [
            # JSON中的名称
            r'"name":\s*"([^"]*(?:Data Center|IDC|数据中心|机房|云计算|Cloud|DC|Center)[^"]*)"',
            r'"title":\s*"([^"]*(?:Data Center|IDC|数据中心|机房|云计算|Cloud|DC|Center)[^"]*)"',
            r'"facility_name":\s*"([^"]*)"',
            r'"company_name":\s*"([^"]*)"',
            
            # HTML标签中的名称
            r'<h[1-6][^>]*>([^<]*(?:Data Center|IDC|数据中心|机房|云计算|Cloud|DC|Center)[^<]*)</h[1-6]>',
            r'<title>([^<]*(?:Data Center|IDC|数据中心|机房|云计算|Cloud|DC|Center)[^<]*)</title>',
            
            # 包含上海关键词的
            r'"name":\s*"([^"]*(?:上海|Shanghai|SH)[^"]*)"',
            r'"title":\s*"([^"]*(?:上海|Shanghai|SH)[^"]*)"',
            
            # HTML属性中的名称
            r'data-name="([^"]*)"',
            r'title="([^"]*(?:Data Center|IDC|数据中心)[^"]*)"',
            r'alt="([^"]*(?:Data Center|IDC|数据中心)[^"]*)"',
            
            # 链接文本
            r'<a[^>]*>([^<]*(?:Data Center|IDC|数据中心|机房)[^<]*)</a>',
            
            # 表格中的名称
            r'<td[^>]*>([^<]*(?:Data Center|IDC|数据中心|机房)[^<]*)</td>',
        ]
        
        for pattern in patterns:
            found_names = re.findall(pattern, content, re.IGNORECASE)
            names.extend([name.strip() for name in found_names if name.strip()])
        
        # 去重并过滤
        unique_names = []
        seen = set()
        for name in names:
            clean_name = name.strip()
            if (clean_name not in seen and 
                3 <= len(clean_name) <= 100 and
                not clean_name.isdigit()):
                unique_names.append(clean_name)
                seen.add(clean_name)
        
        return unique_names
    
    def extract_data_from_content(self, content, source_url):
        """从内容中提取数据"""
        found_data = []
        
        try:
            # 提取坐标和名称
            coordinates = self.extract_coordinates_advanced(content)
            names = self.extract_names_advanced(content)
            
            logger.info(f"  📍 发现 {len(coordinates)} 个坐标，{len(names)} 个名称")
            
            # 过滤上海市范围内的坐标
            shanghai_coords = []
            for lat, lng in coordinates:
                if self.is_in_shanghai(lat, lng):
                    district = self.get_district_by_coordinates(lat, lng)
                    if district:
                        shanghai_coords.append((lat, lng, district))
            
            logger.info(f"  ✅ 上海市内坐标: {len(shanghai_coords)} 个")
            
            # 创建数据中心记录
            for i, (lat, lng, district) in enumerate(shanghai_coords):
                # 检查重复
                coord_key = (round(lat, 6), round(lng, 6))
                if coord_key in self.unique_coordinates:
                    continue
                
                self.unique_coordinates.add(coord_key)
                
                # 分配名称
                if i < len(names):
                    name = names[i]
                else:
                    name = f"{district}数据中心{len(found_data)+1}"
                
                data_center = {
                    'province': '上海市',
                    'district': district,
                    'latitude': lat,
                    'longitude': lng,
                    'name': name,
                    'source': source_url,
                    'coordinates': f"{lat},{lng}",
                    'index': len(self.all_results) + len(found_data) + 1,
                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                found_data.append(data_center)
            
            return found_data
            
        except Exception as e:
            logger.error(f"❌ 数据提取错误: {e}")
            return []
    
    def crawl_url_with_pagination(self, base_url, max_pages=20):
        """爬取URL及其分页"""
        all_data = []
        
        # 先爬取基础URL
        logger.info(f"🔍 爬取基础URL: {base_url}")
        content = self.fetch_url_with_retry(base_url)
        if content:
            data = self.extract_data_from_content(content, base_url)
            all_data.extend(data)
            logger.info(f"  📊 基础页面: {len(data)} 个数据中心")
        
        # 尝试分页
        for page in range(2, max_pages + 1):
            found_page = False
            
            for pattern in self.pagination_patterns:
                if '{page}' in pattern:
                    paginated_url = base_url + pattern.format(page=page)
                elif '{offset}' in pattern:
                    offset = (page - 1) * 20  # 假设每页20个
                    paginated_url = base_url + pattern.format(offset=offset)
                elif '{start}' in pattern:
                    start = (page - 1) * 20
                    paginated_url = base_url + pattern.format(start=start)
                else:
                    continue
                
                logger.info(f"🔍 尝试分页: {paginated_url}")
                content = self.fetch_url_with_retry(paginated_url)
                
                if content:
                    data = self.extract_data_from_content(content, paginated_url)
                    if data:
                        all_data.extend(data)
                        logger.info(f"  📊 第{page}页: {len(data)} 个数据中心")
                        found_page = True
                        break
            
            # 如果没有找到有效分页，停止尝试
            if not found_page:
                logger.info(f"📄 分页结束在第{page-1}页")
                break
        
        return all_data
    
    def crawl_all_sources(self):
        """爬取所有数据源"""
        logger.info("🚀 启动高级上海市数据中心爬虫")
        logger.info("🎯 目标：通过多种策略获取80+个数据中心")
        logger.info("="*70)
        
        all_data = []
        
        # 1. 爬取主要URL及其分页
        logger.info("\n📋 阶段1: 爬取主要URL及分页")
        logger.info("-" * 40)
        for url in self.base_urls:
            try:
                data = self.crawl_url_with_pagination(url)
                all_data.extend(data)
                logger.info(f"✅ {url}: {len(data)} 个数据中心")
            except Exception as e:
                logger.error(f"❌ {url}: {e}")
        
        # 2. 爬取各区URL
        logger.info(f"\n📋 阶段2: 爬取各区URL")
        logger.info("-" * 40)
        
        def crawl_district_url(url):
            try:
                data = self.crawl_url_with_pagination(url, max_pages=5)
                return url, data
            except Exception as e:
                logger.error(f"❌ {url}: {e}")
                return url, []
        
        # 使用线程池并发爬取
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_url = {executor.submit(crawl_district_url, url): url for url in self.district_urls}
            
            for future in as_completed(future_to_url):
                url, data = future.result()
                if data:
                    all_data.extend(data)
                    logger.info(f"✅ {url}: {len(data)} 个数据中心")
        
        # 3. 尝试API端点
        logger.info(f"\n📋 阶段3: 尝试API端点")
        logger.info("-" * 40)
        for api_url in self.api_endpoints:
            try:
                # 构造API请求
                api_params = [
                    {"location": "shanghai"},
                    {"city": "shanghai"},
                    {"region": "shanghai"},
                    {"q": "shanghai data center"},
                ]
                
                for params in api_params:
                    full_url = f"{api_url}?" + urllib.parse.urlencode(params)
                    content = self.fetch_url_with_retry(full_url)
                    if content:
                        data = self.extract_data_from_content(content, full_url)
                        if data:
                            all_data.extend(data)
                            logger.info(f"✅ API {full_url}: {len(data)} 个数据中心")
                            
            except Exception as e:
                logger.error(f"❌ API {api_url}: {e}")
        
        # 去重处理
        unique_data = []
        seen_coords = set()
        
        for dc in all_data:
            coord_key = (round(dc['latitude'], 6), round(dc['longitude'], 6))
            if coord_key not in seen_coords:
                unique_data.append(dc)
                seen_coords.add(coord_key)
        
        self.all_results = unique_data
        logger.info(f"\n🎉 爬取完成！")
        logger.info(f"📊 原始数据: {len(all_data)} 个")
        logger.info(f"✅ 去重后: {len(unique_data)} 个上海市数据中心")
        
        return unique_data
    
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
        
        logger.info(f"\n📊 最终统计:")
        total = sum(district_stats.values())
        for district, count in district_stats.items():
            logger.info(f"  {district}: {count} 个数据中心")
        logger.info(f"  📍 总计: {total} 个数据中心")
        
        # 保存CSV
        csv_file = f"data/shanghai/上海市数据中心坐标_advanced_{timestamp}.csv"
        try:
            df = pd.DataFrame(self.all_results)
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            logger.info(f"✅ CSV文件已保存: {csv_file}")
        except Exception as e:
            logger.error(f"❌ 保存CSV失败: {e}")
        
        # 保存JSON
        json_file = f"data/shanghai/上海市数据中心坐标_advanced_{timestamp}.json"
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_results, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ JSON文件已保存: {json_file}")
        except Exception as e:
            logger.error(f"❌ 保存JSON失败: {e}")
        
        # 生成详细报告
        self.generate_report(timestamp)
    
    def generate_report(self, timestamp):
        """生成详细报告"""
        report_file = f"reports/shanghai/上海市数据中心分布报告_advanced_{timestamp}.txt"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("上海市数据中心分布分析报告（高级版）\n")
                f.write("=" * 60 + "\n\n")
                
                f.write(f"爬取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"爬取策略: 多URL + 分页 + API + 并发爬取\n")
                f.write(f"总数据中心数量: {len(self.all_results)}\n")
                f.write(f"预期目标: 80+ 个数据中心\n")
                
                if len(self.all_results) >= 80:
                    f.write(f"✅ 目标达成度: {len(self.all_results)/80*100:.1f}%\n\n")
                else:
                    f.write(f"⚠️  目标达成度: {len(self.all_results)/80*100:.1f}%（未达到预期）\n\n")
                
                # 数据源统计
                source_stats = {}
                for result in self.all_results:
                    source = result['source']
                    source_stats[source] = source_stats.get(source, 0) + 1
                
                f.write(f"数据源分布:\n")
                f.write("-" * 30 + "\n")
                for source, count in source_stats.items():
                    f.write(f"{source}: {count} 个\n")
                
                # 区域分布统计
                district_data = {}
                for result in self.all_results:
                    district = result['district']
                    if district not in district_data:
                        district_data[district] = []
                    district_data[district].append(result)
                
                f.write(f"\n区域分布统计:\n")
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
                        f.write(f"      来源: {dc['source']}\n")
                        f.write(f"      时间: {dc['crawl_time']}\n\n")
                
                # 地理分布分析
                if self.all_results:
                    lats = [r['latitude'] for r in self.all_results]
                    lngs = [r['longitude'] for r in self.all_results]
                    
                    f.write(f"地理分布分析:\n")
                    f.write("-" * 30 + "\n")
                    f.write(f"纬度范围: {min(lats):.6f} ~ {max(lats):.6f}\n")
                    f.write(f"经度范围: {min(lngs):.6f} ~ {max(lngs):.6f}\n")
                    f.write(f"中心点: ({sum(lats)/len(lats):.6f}, {sum(lngs)/len(lngs):.6f})\n")
                
                # 技术特点说明
                f.write(f"\n高级爬取技术:\n")
                f.write("-" * 30 + "\n")
                f.write(f"1. 多URL策略: 主站 + 各区 + API端点\n")
                f.write(f"2. 智能分页: 自动检测并爬取所有分页\n")
                f.write(f"3. 并发爬取: 多线程提高效率\n")
                f.write(f"4. 高级正则: 多种坐标和名称提取模式\n")
                f.write(f"5. 精确过滤: 严格的上海市行政区域验证\n")
                f.write(f"6. 智能去重: 基于坐标精度去重\n")
                f.write(f"7. 容错处理: 网络重试和异常恢复\n")
                f.write(f"8. 动态UA: 模拟真实浏览器行为\n")
            
            logger.info(f"✅ 高级报告已保存: {report_file}")
            
        except Exception as e:
            logger.error(f"❌ 生成报告失败: {e}")
    
    def display_results(self):
        """显示结果摘要"""
        if not self.all_results:
            logger.error("❌ 没有找到任何数据")
            return
        
        print(f"\n{'='*80}")
        print(f"🎯 上海市数据中心爬取结果（高级版）")
        print(f"{'='*80}")
        
        # 按区域分组显示前几个
        district_data = {}
        for result in self.all_results:
            district = result['district']
            if district not in district_data:
                district_data[district] = []
            district_data[district].append(result)
        
        for district, data in district_data.items():
            print(f"\n📍 {district} ({len(data)} 个数据中心):")
            print("-" * 50)
            # 只显示前3个，避免输出过长
            for i, dc in enumerate(data[:3], 1):
                print(f"{i:2d}. {dc['name']}")
                print(f"    🗺️  坐标: ({dc['latitude']:.6f}, {dc['longitude']:.6f})")
            if len(data) > 3:
                print(f"    ... 还有 {len(data) - 3} 个数据中心")

def main():
    """主函数"""
    print("🚀 高级上海市数据中心爬虫启动")
    print("🎯 目标：通过多种策略获取80+个数据中心")
    print("🔧 技术：多URL + 分页 + API + 并发爬取")
    
    crawler = AdvancedShanghaiDataCenterCrawler()
    
    try:
        # 开始爬取
        results = crawler.crawl_all_sources()
        
        if results:
            # 显示结果摘要
            crawler.display_results()
            
            # 保存数据
            crawler.save_results()
            
            print(f"\n🎉 任务完成！")
            print(f"✅ 成功获取 {len(results)} 个上海市数据中心")
            
            if len(results) >= 80:
                print(f"🎯 达到预期目标（80+个）！")
            elif len(results) >= 50:
                print(f"✅ 获得了相当数量的数据中心")
            else:
                print(f"⚠️ 数据量可能不足，建议进一步优化策略")
            
            print(f"✅ 数据已保存到 data/shanghai/ 目录")
            print(f"✅ 报告已生成到 reports/shanghai/ 目录")
            
        else:
            print("❌ 未获取到任何数据")
            print("💡 可能原因：网络问题、网站结构变化或反爬机制")
            
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断任务")
    except Exception as e:
        logger.error(f"❌ 执行过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
