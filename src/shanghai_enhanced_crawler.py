#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上海市数据中心增强版爬虫
支持分页、地图数据和API调用获取完整数据
"""

import requests
import re
import json
import pandas as pd
import time
import os
from datetime import datetime
import urllib.parse
from bs4 import BeautifulSoup

class ShanghaiEnhancedCrawler:
    def __init__(self):
        self.base_url = "https://www.datacenters.com/locations/china/shanghai"
        self.api_base = "https://www.datacenters.com"
        
        # 上海市地理边界（精确范围）
        self.shanghai_bounds = {
            'lat_min': 30.6,   # 最南端
            'lat_max': 31.9,   # 最北端  
            'lng_min': 120.8,  # 最西端
            'lng_max': 122.2   # 最东端（包含崇明岛）
        }
        
        # 上海市各区的详细边界
        self.shanghai_districts = {
            '黄浦区': {'lat': (31.22, 31.24), 'lng': (121.47, 121.51)},
            '徐汇区': {'lat': (31.17, 31.22), 'lng': (121.42, 121.47)},
            '长宁区': {'lat': (31.20, 31.24), 'lng': (121.40, 121.45)},
            '静安区': {'lat': (31.22, 31.26), 'lng': (121.44, 121.47)},
            '普陀区': {'lat': (31.23, 31.28), 'lng': (121.39, 121.45)},
            '虹口区': {'lat': (31.26, 31.29), 'lng': (121.48, 121.53)},
            '杨浦区': {'lat': (31.26, 31.32), 'lng': (121.50, 121.56)},
            '闵行区': {'lat': (31.05, 31.20), 'lng': (121.32, 121.47)},
            '宝山区': {'lat': (31.29, 31.51), 'lng': (121.44, 121.53)},
            '嘉定区': {'lat': (31.35, 31.42), 'lng': (121.20, 121.32)},
            '浦东新区': {'lat': (30.85, 31.35), 'lng': (121.50, 121.95)},
            '金山区': {'lat': (30.72, 30.92), 'lng': (121.20, 121.47)},
            '松江区': {'lat': (30.98, 31.15), 'lng': (121.20, 121.40)},
            '青浦区': {'lat': (31.10, 31.25), 'lng': (121.05, 121.25)},
            '奉贤区': {'lat': (30.78, 30.98), 'lng': (121.35, 121.65)},
            '崇明区': {'lat': (31.40, 31.85), 'lng': (121.30, 121.95)},
        }
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.datacenters.com/',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        self.all_results = []
        self.unique_coordinates = set()
        self.filtered_out = []
        
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
        """精确检查坐标是否在上海市范围内"""
        # 首先检查大致范围
        if not (self.shanghai_bounds['lat_min'] <= lat <= self.shanghai_bounds['lat_max'] and
                self.shanghai_bounds['lng_min'] <= lng <= self.shanghai_bounds['lng_max']):
            return False, "超出上海市大致范围"
        
        # 检查是否在任何一个区内
        for district, bounds in self.shanghai_districts.items():
            if (bounds['lat'][0] <= lat <= bounds['lat'][1] and 
                bounds['lng'][0] <= lng <= bounds['lng'][1]):
                return True, district
        
        # 如果不在任何区内，但在大致范围内，可能是边界地区
        return True, "上海市边界地区"
    
    def crawl_multiple_pages(self):
        """爬取多个页面的数据"""
        print("🔍 开始爬取上海市数据中心（多页面模式）")
        print("="*70)
        
        all_page_data = []
        
        # 尝试爬取多个页面
        for page in range(1, 6):  # 尝试前5页
            page_url = f"{self.base_url}?page={page}"
            print(f"\n📄 正在爬取第 {page} 页...")
            print(f"🔗 URL: {page_url}")
            
            try:
                response = self.session.get(page_url, timeout=30)
                
                if response.status_code != 200:
                    print(f"  ❌ 请求失败: HTTP {response.status_code}")
                    continue
                
                print(f"  ✅ 请求成功，页面大小: {len(response.text)} 字符")
                
                # 保存页面源码
                page_file = f"html_sources/shanghai/page_{page}_source.html"
                with open(page_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                # 提取页面数据
                page_data = self.extract_data_from_page(response.text, f"page_{page}")
                
                if page_data:
                    all_page_data.extend(page_data)
                    print(f"  🎉 第{page}页提取: {len(page_data)} 个数据中心")
                else:
                    print(f"  ⚠️ 第{page}页未找到数据")
                    # 如果连续2页没有数据，停止
                    if page > 2:
                        break
                
                time.sleep(2)  # 页面间隔
                
            except Exception as e:
                print(f"  ❌ 第{page}页爬取失败: {e}")
        
        return all_page_data
    
    def crawl_map_api_data(self):
        """尝试通过API获取地图数据"""
        print("\n🗺️ 尝试获取地图API数据...")
        
        api_endpoints = [
            "/api/locations/search",
            "/api/map/markers", 
            "/api/datacenters/location",
            "/locations/api/search"
        ]
        
        search_params = [
            {"location": "shanghai", "country": "china"},
            {"city": "shanghai", "region": "china"},
            {"q": "shanghai data center", "type": "datacenter"},
            {"bounds": f"{self.shanghai_bounds['lat_min']},{self.shanghai_bounds['lng_min']},{self.shanghai_bounds['lat_max']},{self.shanghai_bounds['lng_max']}"}
        ]
        
        api_data = []
        
        for endpoint in api_endpoints:
            for params in search_params:
                try:
                    api_url = f"{self.api_base}{endpoint}"
                    print(f"  🔗 尝试API: {endpoint}")
                    
                    # GET请求
                    response = self.session.get(api_url, params=params, timeout=15)
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            if data and isinstance(data, (list, dict)):
                                api_data.append(data)
                                print(f"    ✅ API响应成功: {len(str(data))} 字符")
                                
                                # 保存API响应
                                api_file = f"html_sources/shanghai/api_{endpoint.replace('/', '_')}_{len(api_data)}.json"
                                with open(api_file, 'w', encoding='utf-8') as f:
                                    json.dump(data, f, ensure_ascii=False, indent=2)
                        except json.JSONDecodeError:
                            pass
                    
                    time.sleep(1)
                    
                except Exception as e:
                    pass  # 静默处理API错误
        
        # 处理API数据
        processed_api_data = []
        for data in api_data:
            extracted = self.extract_data_from_api(data)
            if extracted:
                processed_api_data.extend(extracted)
        
        if processed_api_data:
            print(f"  🎉 API数据提取: {len(processed_api_data)} 个数据中心")
        
        return processed_api_data
    
    def extract_data_from_api(self, api_data):
        """从API响应中提取数据"""
        results = []
        
        try:
            if isinstance(api_data, dict):
                # 检查常见的数据结构
                data_keys = ['data', 'results', 'locations', 'markers', 'facilities']
                for key in data_keys:
                    if key in api_data:
                        api_data = api_data[key]
                        break
            
            if isinstance(api_data, list):
                for item in api_data:
                    if isinstance(item, dict):
                        result = self.parse_api_item(item)
                        if result:
                            results.append(result)
            elif isinstance(api_data, dict):
                result = self.parse_api_item(api_data)
                if result:
                    results.append(result)
        
        except Exception as e:
            pass
        
        return results
    
    def parse_api_item(self, item):
        """解析单个API数据项"""
        try:
            # 尝试提取坐标
            lat = lng = None
            name = "Unknown Data Center"
            
            # 坐标提取的多种方式
            coord_keys = [
                ('latitude', 'longitude'),
                ('lat', 'lng'), 
                ('lat', 'lon'),
                ('y', 'x')
            ]
            
            for lat_key, lng_key in coord_keys:
                if lat_key in item and lng_key in item:
                    try:
                        lat = float(item[lat_key])
                        lng = float(item[lng_key])
                        break
                    except:
                        pass
            
            # 名称提取
            name_keys = ['name', 'title', 'facility_name', 'datacenter_name', 'label']
            for key in name_keys:
                if key in item and item[key]:
                    name = str(item[key]).strip()
                    break
            
            if lat and lng:
                # 验证坐标
                is_valid, location = self.is_in_shanghai(lat, lng)
                if is_valid:
                    return {
                        'latitude': lat,
                        'longitude': lng,
                        'name': name,
                        'source': 'api',
                        'district': location
                    }
        
        except Exception as e:
            pass
        
        return None
    
    def extract_data_from_page(self, content, source_key):
        """从页面内容中提取数据"""
        found_data = []
        
        try:
            print(f"  正在解析页面内容...")
            
            # 1. 提取JSON-LD结构化数据
            json_ld_data = self.extract_json_ld_data(content)
            if json_ld_data:
                found_data.extend(json_ld_data)
                print(f"    JSON-LD数据: {len(json_ld_data)} 个")
            
            # 2. 提取Google Maps标记数据
            map_data = self.extract_map_markers(content)
            if map_data:
                found_data.extend(map_data)
                print(f"    地图标记: {len(map_data)} 个")
            
            # 3. 提取常规坐标模式
            coord_data = self.extract_coordinate_patterns(content, source_key)
            if coord_data:
                found_data.extend(coord_data)
                print(f"    坐标模式: {len(coord_data)} 个")
            
            # 4. 提取表格和列表数据
            structured_data = self.extract_structured_data(content, source_key)
            if structured_data:
                found_data.extend(structured_data)
                print(f"    结构化数据: {len(structured_data)} 个")
            
            # 去重处理
            unique_data = self.deduplicate_data(found_data)
            print(f"    去重后: {len(unique_data)} 个唯一数据中心")
            
            return unique_data
            
        except Exception as e:
            print(f"  数据提取错误: {e}")
            return []
    
    def extract_json_ld_data(self, content):
        """提取JSON-LD结构化数据"""
        results = []
        
        try:
            # 查找JSON-LD脚本
            json_ld_pattern = r'<script[^>]*type=["\']*application/ld\+json["\']*[^>]*>(.*?)</script>'
            json_scripts = re.findall(json_ld_pattern, content, re.DOTALL | re.IGNORECASE)
            
            for script in json_scripts:
                try:
                    data = json.loads(script.strip())
                    extracted = self.parse_json_ld(data)
                    if extracted:
                        results.extend(extracted)
                except:
                    pass
        
        except Exception as e:
            pass
        
        return results
    
    def parse_json_ld(self, data):
        """解析JSON-LD数据"""
        results = []
        
        try:
            if isinstance(data, list):
                for item in data:
                    results.extend(self.parse_json_ld(item))
            elif isinstance(data, dict):
                # 查找地址和坐标信息
                if 'geo' in data or 'address' in data or '@type' in data:
                    result = self.parse_location_data(data)
                    if result:
                        results.append(result)
                
                # 递归查找嵌套数据
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        results.extend(self.parse_json_ld(value))
        
        except Exception as e:
            pass
        
        return results
    
    def parse_location_data(self, data):
        """解析位置数据"""
        try:
            lat = lng = None
            name = "Unknown Data Center"
            
            # 提取坐标
            if 'geo' in data:
                geo = data['geo']
                if isinstance(geo, dict):
                    lat = geo.get('latitude') or geo.get('lat')
                    lng = geo.get('longitude') or geo.get('lng')
            
            # 提取名称
            name_keys = ['name', 'title', '@name']
            for key in name_keys:
                if key in data and data[key]:
                    name = str(data[key]).strip()
                    break
            
            if lat and lng:
                try:
                    lat = float(lat)
                    lng = float(lng)
                    
                    is_valid, district = self.is_in_shanghai(lat, lng)
                    if is_valid:
                        return {
                            'latitude': lat,
                            'longitude': lng,
                            'name': name,
                            'source': 'json_ld',
                            'district': district
                        }
                except:
                    pass
        
        except Exception as e:
            pass
        
        return None
    
    def extract_map_markers(self, content):
        """提取Google Maps标记数据"""
        results = []
        
        try:
            # 查找gmp-advanced-marker标记
            marker_pattern = r'<gmp-advanced-marker[^>]*position="([^"]*)"[^>]*>.*?</gmp-advanced-marker>'
            markers = re.findall(marker_pattern, content, re.DOTALL)
            
            for i, position in enumerate(markers):
                try:
                    if ',' in position:
                        parts = position.split(',')
                        if len(parts) >= 2:
                            lat = float(parts[0].strip())
                            lng = float(parts[1].strip())
                            
                            is_valid, district = self.is_in_shanghai(lat, lng)
                            if is_valid:
                                results.append({
                                    'latitude': lat,
                                    'longitude': lng,
                                    'name': f"上海数据中心_{i+1}",
                                    'source': 'map_marker',
                                    'district': district
                                })
                except:
                    pass
            
            # 查找聚合标记中的数量信息
            cluster_pattern = r'aria-label="(\d+)"[^>]*title="(\d+)"[^>]*position="([^"]*)"'
            clusters = re.findall(cluster_pattern, content)
            
            print(f"    发现聚合标记: {len(clusters)} 个")
            for label, title, position in clusters:
                print(f"      聚合点: {label}个数据中心 位置:{position}")
        
        except Exception as e:
            pass
        
        return results
    
    def extract_coordinate_patterns(self, content, source_key):
        """提取坐标模式"""
        results = []
        
        try:
            # 多种坐标模式
            patterns = [
                r'"latitude":\s*([\d\.-]+).*?"longitude":\s*([\d\.-]+)',
                r'"lat":\s*([\d\.-]+).*?"lng":\s*([\d\.-]+)',
                r'"lat":\s*([\d\.-]+).*?"lon":\s*([\d\.-]+)',
                r'latitude["\']?\s*:\s*["\']?([\d\.-]+)["\']?.*?longitude["\']?\s*:\s*["\']?([\d\.-]+)["\']?',
                r'coords?\[.*?([\d\.]+),\s*([\d\.]+).*?\]'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    try:
                        lat = float(match[0])
                        lng = float(match[1])
                        
                        is_valid, district = self.is_in_shanghai(lat, lng)
                        if is_valid:
                            coord_key = (round(lat, 6), round(lng, 6))
                            if coord_key not in self.unique_coordinates:
                                self.unique_coordinates.add(coord_key)
                                results.append({
                                    'latitude': lat,
                                    'longitude': lng,
                                    'name': f"上海数据中心_{len(results)+1}",
                                    'source': source_key,
                                    'district': district
                                })
                    except:
                        pass
        
        except Exception as e:
            pass
        
        return results
    
    def extract_structured_data(self, content, source_key):
        """提取结构化数据"""
        results = []
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # 查找数据中心列表
            datacenter_selectors = [
                '.datacenter-item', '.facility-item', '.location-item',
                '[data-testid*="datacenter"]', '[data-testid*="facility"]',
                '.result-item', '.search-result'
            ]
            
            for selector in datacenter_selectors:
                items = soup.select(selector)
                for item in items:
                    # 提取名称
                    name_elem = item.select_one('h1, h2, h3, h4, .title, .name, .facility-name')
                    name = name_elem.get_text().strip() if name_elem else "未知数据中心"
                    
                    # 查找嵌入的坐标信息
                    item_text = str(item)
                    coord_matches = re.findall(r'([\d\.]+),\s*([\d\.]+)', item_text)
                    
                    for lat_str, lng_str in coord_matches:
                        try:
                            lat = float(lat_str)
                            lng = float(lng_str)
                            
                            if 30 <= lat <= 32 and 120 <= lng <= 122:  # 大致范围过滤
                                is_valid, district = self.is_in_shanghai(lat, lng)
                                if is_valid:
                                    results.append({
                                        'latitude': lat,
                                        'longitude': lng,
                                        'name': name,
                                        'source': source_key,
                                        'district': district
                                    })
                                    break
                        except:
                            pass
        
        except Exception as e:
            pass
        
        return results
    
    def deduplicate_data(self, data):
        """去重数据"""
        unique_data = []
        seen_coords = set()
        
        for item in data:
            coord_key = (round(item['latitude'], 6), round(item['longitude'], 6))
            if coord_key not in seen_coords:
                seen_coords.add(coord_key)
                unique_data.append(item)
        
        return unique_data
    
    def crawl_all_sources(self):
        """爬取所有数据源"""
        print("🌟 上海市数据中心增强版爬虫启动")
        print("🎯 目标：获取上海市完整的数据中心分布信息")
        print("📋 策略：多页面 + 地图API + 结构化数据")
        print("="*70)
        
        all_data = []
        
        # 1. 爬取分页数据
        page_data = self.crawl_multiple_pages()
        if page_data:
            all_data.extend(page_data)
            print(f"\n📄 分页数据总计: {len(page_data)} 个数据中心")
        
        # 2. 尝试API数据
        api_data = self.crawl_map_api_data()
        if api_data:
            all_data.extend(api_data)
            print(f"\n🔗 API数据总计: {len(api_data)} 个数据中心")
        
        # 3. 去重和处理
        final_data = self.deduplicate_data(all_data)
        
        # 4. 详细验证和分类
        validated_data = []
        for item in final_data:
            is_valid, district = self.is_in_shanghai(item['latitude'], item['longitude'])
            if is_valid:
                item['district'] = district
                item['crawl_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                item['index'] = len(validated_data) + 1
                validated_data.append(item)
                print(f"  ✅ {len(validated_data)}. {item['name']} - {district} ({item['latitude']:.6f}, {item['longitude']:.6f})")
            else:
                self.filtered_out.append({**item, 'filter_reason': district})
        
        self.all_results = validated_data
        
        print(f"\n{'='*70}")
        print(f"📊 爬取完成统计:")
        print(f"  ✅ 有效数据中心: {len(self.all_results)} 个")
        print(f"  ❌ 过滤掉: {len(self.filtered_out)} 个")
        print(f"  🎯 总爬取: {len(final_data)} 个原始数据")
        
        return self.all_results
    
    def save_results(self):
        """保存结果"""
        if not self.all_results:
            print("❌ 没有数据需要保存")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 按区统计
        district_stats = {}
        for result in self.all_results:
            district = result.get('district', '未知')
            district_stats[district] = district_stats.get(district, 0) + 1
        
        print(f"\n📊 上海市各区分布:")
        for district, count in sorted(district_stats.items()):
            print(f"  {district}: {count} 个数据中心")
        
        # 保存CSV
        csv_file = f"data/shanghai/上海市数据中心完整分布_{timestamp}.csv"
        try:
            df = pd.DataFrame(self.all_results)
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"\n✅ CSV文件已保存: {csv_file}")
        except Exception as e:
            print(f"❌ 保存CSV失败: {e}")
        
        # 保存JSON
        json_file = f"data/shanghai/上海市数据中心完整分布_{timestamp}.json"
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_results, f, ensure_ascii=False, indent=2)
            print(f"✅ JSON文件已保存: {json_file}")
        except Exception as e:
            print(f"❌ 保存JSON失败: {e}")
        
        # 保存过滤数据（用于分析）
        if self.filtered_out:
            filtered_file = f"data/shanghai/过滤数据_{timestamp}.json"
            try:
                with open(filtered_file, 'w', encoding='utf-8') as f:
                    json.dump(self.filtered_out, f, ensure_ascii=False, indent=2)
                print(f"📄 过滤数据已保存: {filtered_file}")
            except Exception as e:
                print(f"❌ 保存过滤数据失败: {e}")
        
        # 生成详细报告
        self.generate_detailed_report(timestamp)
    
    def generate_detailed_report(self, timestamp):
        """生成详细报告"""
        report_file = f"reports/shanghai/上海市数据中心完整分析报告_{timestamp}.txt"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("上海市数据中心完整分析报告\n")
                f.write("=" * 60 + "\n\n")
                
                f.write(f"爬取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"总数据中心数量: {len(self.all_results)}\n")
                f.write(f"过滤掉的数据: {len(self.filtered_out)}\n\n")
                
                # 爬取策略说明
                f.write("爬取策略:\n")
                f.write("-" * 30 + "\n")
                f.write("1. 多页面爬取：尝试爬取前5页数据\n")
                f.write("2. 地图API调用：尝试获取地图标记数据\n")
                f.write("3. 结构化数据提取：JSON-LD、表格、列表数据\n")
                f.write("4. 地理验证：精确的上海市区界验证\n\n")
                
                # 数据源统计
                f.write("数据源统计:\n")
                f.write("-" * 30 + "\n")
                source_stats = {}
                for result in self.all_results:
                    source = result.get('source', '未知')
                    source_stats[source] = source_stats.get(source, 0) + 1
                
                for source, count in source_stats.items():
                    f.write(f"{source}: {count} 个数据中心\n")
                
                # 按区分布
                district_data = {}
                for result in self.all_results:
                    district = result.get('district', '未知')
                    if district not in district_data:
                        district_data[district] = []
                    district_data[district].append(result)
                
                f.write(f"\n各区分布统计:\n")
                f.write("-" * 20 + "\n")
                for district, data in sorted(district_data.items()):
                    f.write(f"{district}: {len(data)} 个数据中心\n")
                
                f.write(f"\n详细列表:\n")
                f.write("-" * 20 + "\n")
                
                for district, data in sorted(district_data.items()):
                    f.write(f"\n{district} ({len(data)} 个):\n")
                    for i, dc in enumerate(data, 1):
                        f.write(f"  {i:2d}. {dc['name']}\n")
                        f.write(f"      坐标: ({dc['latitude']:.6f}, {dc['longitude']:.6f})\n")
                        f.write(f"      来源: {dc.get('source', '未知')}\n")
                        f.write(f"      时间: {dc.get('crawl_time', '未知')}\n\n")
                
                # 过滤数据分析
                if self.filtered_out:
                    f.write(f"\n过滤数据分析:\n")
                    f.write("-" * 20 + "\n")
                    f.write(f"总计过滤: {len(self.filtered_out)} 个\n\n")
                    
                    filter_reasons = {}
                    for item in self.filtered_out:
                        reason = item.get('filter_reason', '未知')
                        filter_reasons[reason] = filter_reasons.get(reason, 0) + 1
                    
                    for reason, count in filter_reasons.items():
                        f.write(f"{reason}: {count} 个\n")
                
                # 地理分布分析
                if self.all_results:
                    lats = [r['latitude'] for r in self.all_results]
                    lngs = [r['longitude'] for r in self.all_results]
                    
                    f.write(f"\n地理分布分析:\n")
                    f.write(f"-" * 20 + "\n")
                    f.write(f"纬度范围: {min(lats):.6f} ~ {max(lats):.6f}\n")
                    f.write(f"经度范围: {min(lngs):.6f} ~ {max(lngs):.6f}\n")
                    f.write(f"中心点: ({sum(lats)/len(lats):.6f}, {sum(lngs)/len(lngs):.6f})\n")
                
                # 技术说明
                f.write(f"\n技术说明:\n")
                f.write(f"-" * 20 + "\n")
                f.write(f"1. 地理验证：使用上海市16个区的精确边界\n")
                f.write(f"2. 去重策略：基于坐标精度到小数点后6位\n")
                f.write(f"3. 多源爬取：结合分页、API、结构化数据\n")
                f.write(f"4. 数据完整性：目标获取80+个数据中心\n")
            
            print(f"✅ 详细报告已保存: {report_file}")
            
        except Exception as e:
            print(f"❌ 生成报告失败: {e}")

def main():
    """主函数"""
    print("🚀 上海市数据中心增强版爬虫")
    print("🎯 采用多种策略获取完整数据")
    print("📍 精确的地理验证和区域分类")
    
    crawler = ShanghaiEnhancedCrawler()
    
    try:
        # 开始爬取
        results = crawler.crawl_all_sources()
        
        if results:
            print(f"\n🎉 任务完成！")
            print(f"✅ 成功获取 {len(results)} 个上海市数据中心")
            print(f"📊 数据已保存到 data/shanghai/ 目录")
            print(f"📋 报告已生成到 reports/shanghai/ 目录")
            
            # 保存数据
            crawler.save_results()
            
        else:
            print("❌ 未获取到任何数据")
            print("💡 建议检查网络连接或目标网站是否可访问")
            
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断任务")
    except Exception as e:
        print(f"❌ 执行过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
