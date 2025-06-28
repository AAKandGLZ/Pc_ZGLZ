#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上海市数据中心聚合数据解析器
专门处理地图聚合标记和隐藏数据
"""

import requests
import re
import json
import pandas as pd
import time
import os
from datetime import datetime
from urllib.parse import urlencode, parse_qs, urlparse

class ShanghaiClusterCrawler:
    def __init__(self):
        self.base_url = "https://www.datacenters.com/locations/china/shanghai"
        
        # 从您提供的聚合标记中提取的坐标点
        self.cluster_points = [
            {"lat": 30.765168, "lng": 120.709018, "count": "unknown"},
            {"lat": 30.8556073, "lng": 121.0881835, "count": "unknown"},
            {"lat": 29.88112907600477, "lng": 121.6189134120941, "count": 6},
            {"lat": 30.866923071457734, "lng": 120.135498046875, "count": 2},
            {"lat": 31.247448448494325, "lng": 121.5220758526824, "count": 86}, # 主要聚合点！
            {"lat": 31.280839522072, "lng": 120.62127828598022, "count": 5},
            {"lat": 31.348264727716113, "lng": 119.82238054275511, "count": 3},
            {"lat": 31.41220361509835, "lng": 121.04774951934814, "count": 4},
            {"lat": 31.533138994778028, "lng": 120.3129905462265, "count": 4},
            {"lat": 31.703637759244117, "lng": 120.92243671417236, "count": 3},
            {"lat": 31.748243980827056, "lng": 119.94232892990111, "count": 3},
            {"lat": 31.967395368542427, "lng": 120.74172377586363, "count": 6},
        ]
        
        # 上海市精确边界
        self.shanghai_bounds = {
            'lat_min': 30.6, 'lat_max': 31.9,
            'lng_min': 120.8, 'lng_max': 122.2
        }
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.datacenters.com/locations/china/shanghai',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        self.all_results = []
        self.cluster_details = []
        
        # 创建输出目录
        os.makedirs("data/shanghai", exist_ok=True)
        os.makedirs("reports/shanghai", exist_ok=True)
        os.makedirs("html_sources/shanghai", exist_ok=True)
    
    def analyze_cluster_requests(self):
        """分析聚合点的请求模式"""
        print("🔍 分析地图聚合点请求模式...")
        
        # 尝试多种可能的API端点
        api_patterns = [
            "/api/v1/locations/clusters",
            "/api/v2/locations/search", 
            "/api/map/clusters",
            "/api/locations/markers",
            "/locations/clusters",
            "/search/locations",
            "/api/facilities/search",
            "/v1/datacenters/search"
        ]
        
        # 不同的缩放级别和边界参数
        zoom_levels = [8, 9, 10, 11, 12, 13, 14, 15, 16]
        
        cluster_data = []
        
        for zoom in zoom_levels:
            print(f"\n🔍 测试缩放级别: {zoom}")
            
            # 计算不同缩放级别的边界
            bounds = self.calculate_bounds_for_zoom(zoom)
            
            for api_pattern in api_patterns:
                try:
                    # 构建API URL
                    api_url = f"https://www.datacenters.com{api_pattern}"
                    
                    # 尝试不同的参数组合
                    param_sets = [
                        {
                            'zoom': zoom,
                            'bounds': f"{bounds['sw_lat']},{bounds['sw_lng']},{bounds['ne_lat']},{bounds['ne_lng']}"
                        },
                        {
                            'z': zoom,
                            'bbox': f"{bounds['sw_lng']},{bounds['sw_lat']},{bounds['ne_lng']},{bounds['ne_lat']}"
                        },
                        {
                            'zoom': zoom,
                            'lat': 31.2304,
                            'lng': 121.4737,
                            'radius': 50
                        },
                        {
                            'location': 'shanghai',
                            'zoom': zoom,
                            'clustering': 'true'
                        }
                    ]
                    
                    for params in param_sets:
                        try:
                            response = self.session.get(api_url, params=params, timeout=10)
                            
                            if response.status_code == 200:
                                try:
                                    data = response.json()
                                    if data and (isinstance(data, list) or 
                                                (isinstance(data, dict) and len(data) > 0)):
                                        
                                        print(f"    ✅ API成功: {api_pattern} (zoom={zoom})")
                                        print(f"       数据长度: {len(str(data))} 字符")
                                        
                                        # 保存API响应
                                        api_file = f"html_sources/shanghai/cluster_api_{api_pattern.replace('/', '_')}_z{zoom}_{len(cluster_data)}.json"
                                        with open(api_file, 'w', encoding='utf-8') as f:
                                            json.dump(data, f, ensure_ascii=False, indent=2)
                                        
                                        cluster_data.append({
                                            'api': api_pattern,
                                            'zoom': zoom,
                                            'params': params,
                                            'data': data
                                        })
                                        
                                        # 解析数据
                                        parsed = self.parse_cluster_api_data(data)
                                        if parsed:
                                            print(f"       解析出: {len(parsed)} 个数据点")
                                        
                                except json.JSONDecodeError:
                                    # 不是JSON数据，可能是HTML或其他格式
                                    if len(response.text) > 100:
                                        print(f"    📄 非JSON响应: {api_pattern} (zoom={zoom}) - {len(response.text)} 字符")
                                        
                                        # 保存非JSON响应
                                        html_file = f"html_sources/shanghai/cluster_response_{api_pattern.replace('/', '_')}_z{zoom}.html"
                                        with open(html_file, 'w', encoding='utf-8') as f:
                                            f.write(response.text)
                            
                            time.sleep(0.5)  # 避免请求过快
                            
                        except Exception as e:
                            pass  # 静默处理单个请求错误
                            
                except Exception as e:
                    pass  # 静默处理API错误
        
        return cluster_data
    
    def calculate_bounds_for_zoom(self, zoom):
        """根据缩放级别计算边界"""
        # 上海市中心点
        center_lat = 31.2304
        center_lng = 121.4737
        
        # 根据缩放级别计算范围
        zoom_factor = 1.0 / (2 ** (zoom - 10))
        
        lat_delta = 0.5 * zoom_factor
        lng_delta = 0.5 * zoom_factor
        
        return {
            'sw_lat': center_lat - lat_delta,
            'sw_lng': center_lng - lng_delta,
            'ne_lat': center_lat + lat_delta,
            'ne_lng': center_lng + lng_delta
        }
    
    def parse_cluster_api_data(self, data):
        """解析聚合API数据"""
        results = []
        
        try:
            if isinstance(data, dict):
                # 检查常见的数据键
                for key in ['clusters', 'markers', 'facilities', 'locations', 'data', 'results']:
                    if key in data:
                        results.extend(self.parse_cluster_api_data(data[key]))
                
                # 检查是否是单个数据点
                if 'lat' in data or 'latitude' in data:
                    parsed = self.parse_single_location(data)
                    if parsed:
                        results.append(parsed)
            
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        parsed = self.parse_single_location(item)
                        if parsed:
                            results.append(parsed)
        
        except Exception as e:
            pass
        
        return results
    
    def parse_single_location(self, item):
        """解析单个位置数据"""
        try:
            lat = lng = None
            name = "Unknown Data Center"
            count = 1
            
            # 提取坐标
            if 'lat' in item and 'lng' in item:
                lat, lng = float(item['lat']), float(item['lng'])
            elif 'latitude' in item and 'longitude' in item:
                lat, lng = float(item['latitude']), float(item['longitude'])
            elif 'y' in item and 'x' in item:
                lat, lng = float(item['y']), float(item['x'])
            
            # 提取名称
            for key in ['name', 'title', 'label', 'facility_name']:
                if key in item and item[key]:
                    name = str(item[key]).strip()
                    break
            
            # 提取数量（聚合点）
            for key in ['count', 'cluster_count', 'facilities_count', 'size']:
                if key in item:
                    try:
                        count = int(item[key])
                        break
                    except:
                        pass
            
            if lat and lng and self.is_in_shanghai_area(lat, lng):
                return {
                    'latitude': lat,
                    'longitude': lng,
                    'name': name,
                    'count': count,
                    'source': 'cluster_api'
                }
        
        except Exception as e:
            pass
        
        return None
    
    def is_in_shanghai_area(self, lat, lng):
        """检查是否在上海市区域内（宽松检查）"""
        return (30.5 <= lat <= 32.0 and 120.5 <= lng <= 122.5)
    
    def crawl_detailed_locations(self):
        """针对聚合点爬取详细位置"""
        print("\n🎯 针对聚合点爬取详细位置...")
        
        detailed_results = []
        
        # 重点关注有86个数据中心的聚合点
        main_cluster = {"lat": 31.247448448494325, "lng": 121.5220758526824, "count": 86}
        
        print(f"🔍 重点分析主聚合点: ({main_cluster['lat']:.6f}, {main_cluster['lng']:.6f}) - {main_cluster['count']}个数据中心")
        
        # 围绕主聚合点进行细分爬取
        detailed_results.extend(self.crawl_cluster_details(main_cluster))
          # 处理其他聚合点
        for cluster in self.cluster_points:
            count = cluster.get('count', 0)
            if isinstance(count, str):
                try:
                    count = int(count)
                except:
                    count = 0
            
            if count > 2:  # 只处理数量较多的聚合点
                print(f"🔍 分析聚合点: ({cluster['lat']:.6f}, {cluster['lng']:.6f}) - {count}个")
                cluster_details = self.crawl_cluster_details(cluster)
                detailed_results.extend(cluster_details)
                time.sleep(1)
        
        return detailed_results
    
    def crawl_cluster_details(self, cluster):
        """爬取单个聚合点的详细信息"""
        results = []
        
        try:
            # 尝试多种详细查询方式
            detail_strategies = [
                self.crawl_by_radius_zoom,
                self.crawl_by_grid_subdivision,
                self.crawl_by_facility_ids
            ]
            
            for strategy in detail_strategies:
                try:
                    strategy_results = strategy(cluster)
                    if strategy_results:
                        results.extend(strategy_results)
                        print(f"    策略 {strategy.__name__}: 获取 {len(strategy_results)} 个结果")
                except Exception as e:
                    pass
        
        except Exception as e:
            pass
        
        return results
    
    def crawl_by_radius_zoom(self, cluster):
        """通过半径缩放爬取"""
        results = []
        
        # 尝试不同的半径和缩放级别
        radii = [1, 2, 5, 10, 20, 50]  # 公里
        zoom_levels = [12, 13, 14, 15, 16, 17, 18]
        
        for radius in radii:
            for zoom in zoom_levels:
                try:
                    # 构建请求URL
                    params = {
                        'lat': cluster['lat'],
                        'lng': cluster['lng'],
                        'radius': radius,
                        'zoom': zoom,
                        'format': 'json'
                    }
                    
                    # 尝试不同的端点
                    endpoints = [
                        '/api/locations/nearby',
                        '/api/facilities/radius',
                        '/locations/search',
                        '/api/search'
                    ]
                    
                    for endpoint in endpoints:
                        try:
                            url = f"https://www.datacenters.com{endpoint}"
                            response = self.session.get(url, params=params, timeout=10)
                            
                            if response.status_code == 200:
                                try:
                                    data = response.json()
                                    parsed = self.parse_cluster_api_data(data)
                                    if parsed:
                                        results.extend(parsed)
                                        
                                        # 保存成功的响应
                                        file_name = f"html_sources/shanghai/radius_{endpoint.replace('/', '_')}_r{radius}_z{zoom}.json"
                                        with open(file_name, 'w', encoding='utf-8') as f:
                                            json.dump(data, f, ensure_ascii=False, indent=2)
                                except:
                                    pass
                        except:
                            pass
                    
                    time.sleep(0.3)
                    
                except Exception as e:
                    pass
        
        return results
    
    def crawl_by_grid_subdivision(self, cluster):
        """通过网格细分爬取"""
        results = []
        
        # 围绕聚合点创建网格
        grid_size = 0.01  # 约1公里
        grid_range = 0.05  # 总范围约5公里
        
        lat_start = cluster['lat'] - grid_range
        lng_start = cluster['lng'] - grid_range
        
        grid_points = []
        lat = lat_start
        while lat <= cluster['lat'] + grid_range:
            lng = lng_start
            while lng <= cluster['lng'] + grid_range:
                grid_points.append({'lat': lat, 'lng': lng})
                lng += grid_size
            lat += grid_size
        
        print(f"    创建 {len(grid_points)} 个网格点进行细分查询")
        
        for i, point in enumerate(grid_points):
            if i % 10 == 0:  # 只查询部分网格点，避免过多请求
                try:
                    # 针对每个网格点进行精确查询
                    params = {
                        'lat': point['lat'],
                        'lng': point['lng'],
                        'precision': 'high',
                        'limit': 50
                    }
                    
                    url = f"https://www.datacenters.com/api/locations/point"
                    response = self.session.get(url, params=params, timeout=5)
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            parsed = self.parse_cluster_api_data(data)
                            if parsed:
                                results.extend(parsed)
                        except:
                            pass
                    
                    time.sleep(0.2)
                    
                except Exception as e:
                    pass
        
        return results
    
    def crawl_by_facility_ids(self, cluster):
        """通过设施ID爬取"""
        results = []
        
        # 尝试猜测设施ID范围（基于常见模式）
        try:
            # 基于坐标生成可能的ID
            base_id = int((cluster['lat'] * 1000 + cluster['lng'] * 1000) % 10000)
            
            id_ranges = [
                range(base_id, base_id + 100),
                range(1, 1000),  # 常见的ID范围
                range(10000, 10500),
                range(20000, 20200)
            ]
            
            for id_range in id_ranges:
                for facility_id in list(id_range)[::10]:  # 每10个ID测试一个
                    try:
                        url = f"https://www.datacenters.com/api/facilities/{facility_id}"
                        response = self.session.get(url, timeout=5)
                        
                        if response.status_code == 200:
                            try:
                                data = response.json()
                                parsed = self.parse_single_location(data)
                                if parsed and self.is_in_shanghai_area(parsed['latitude'], parsed['longitude']):
                                    results.append(parsed)
                            except:
                                pass
                        
                        time.sleep(0.1)
                        
                    except Exception as e:
                        pass
        
        except Exception as e:
            pass
        
        return results
    
    def run_comprehensive_crawl(self):
        """运行综合爬取"""
        print("🚀 上海市数据中心聚合数据解析器启动")
        print("🎯 专门处理地图聚合标记和隐藏数据")
        print("📊 目标：解析86+个数据中心聚合点")
        print("="*70)
        
        all_results = []
        
        # 1. 分析聚合请求模式
        print("\n🔍 阶段1: 分析地图聚合API模式")
        cluster_api_data = self.analyze_cluster_requests()
        
        if cluster_api_data:
            print(f"✅ 发现 {len(cluster_api_data)} 个API响应")
            for api_response in cluster_api_data:
                parsed = self.parse_cluster_api_data(api_response['data'])
                if parsed:
                    all_results.extend(parsed)
        
        # 2. 详细位置爬取
        print("\n🔍 阶段2: 聚合点详细位置爬取")
        detailed_results = self.crawl_detailed_locations()
        if detailed_results:
            all_results.extend(detailed_results)
        
        # 3. 去重和验证
        unique_results = self.deduplicate_results(all_results)
        
        # 4. 最终验证和分类
        final_results = []
        for result in unique_results:
            if self.is_in_shanghai_area(result['latitude'], result['longitude']):
                result['crawl_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                result['index'] = len(final_results) + 1
                final_results.append(result)
                print(f"  ✅ {len(final_results)}. {result['name']} ({result['latitude']:.6f}, {result['longitude']:.6f}) [数量:{result.get('count', 1)}]")
        
        self.all_results = final_results
        
        print(f"\n{'='*70}")
        print(f"📊 聚合解析完成统计:")
        print(f"  ✅ 解析出数据中心: {len(self.all_results)} 个")
        print(f"  📍 聚合点总数量: {sum(r.get('count', 1) for r in self.all_results)}")
        
        return self.all_results
    
    def deduplicate_results(self, results):
        """去重结果"""
        unique_results = []
        seen_coords = set()
        
        for result in results:
            coord_key = (round(result['latitude'], 6), round(result['longitude'], 6))
            if coord_key not in seen_coords:
                seen_coords.add(coord_key)
                unique_results.append(result)
        
        return unique_results
    
    def save_results(self):
        """保存结果"""
        if not self.all_results:
            print("❌ 没有数据需要保存")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 统计聚合数量
        total_count = sum(result.get('count', 1) for result in self.all_results)
        
        print(f"\n📊 聚合数据统计:")
        print(f"  解析的聚合点: {len(self.all_results)} 个")
        print(f"  估计总数据中心: {total_count} 个")
        
        # 保存CSV
        csv_file = f"data/shanghai/上海市聚合数据中心_{timestamp}.csv"
        try:
            df = pd.DataFrame(self.all_results)
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"\n✅ CSV文件已保存: {csv_file}")
        except Exception as e:
            print(f"❌ 保存CSV失败: {e}")
        
        # 保存JSON
        json_file = f"data/shanghai/上海市聚合数据中心_{timestamp}.json"
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_results, f, ensure_ascii=False, indent=2)
            print(f"✅ JSON文件已保存: {json_file}")
        except Exception as e:
            print(f"❌ 保存JSON失败: {e}")
        
        # 生成聚合分析报告
        self.generate_cluster_report(timestamp, total_count)
    
    def generate_cluster_report(self, timestamp, total_count):
        """生成聚合分析报告"""
        report_file = f"reports/shanghai/上海市聚合数据分析_{timestamp}.txt"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("上海市数据中心聚合数据分析报告\n")
                f.write("=" * 60 + "\n\n")
                
                f.write(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"解析聚合点数量: {len(self.all_results)}\n")
                f.write(f"估计总数据中心数量: {total_count}\n\n")
                
                f.write("聚合解析策略:\n")
                f.write("-" * 30 + "\n")
                f.write("1. API模式分析：测试多种缩放级别和边界参数\n")
                f.write("2. 半径缩放：围绕聚合点进行半径查询\n")
                f.write("3. 网格细分：将聚合区域细分为网格进行查询\n")
                f.write("4. 设施ID：通过ID范围猜测进行查询\n\n")
                
                f.write("发现的聚合点:\n")
                f.write("-" * 30 + "\n")
                for i, result in enumerate(self.all_results, 1):
                    f.write(f"{i:2d}. {result['name']}\n")
                    f.write(f"    坐标: ({result['latitude']:.6f}, {result['longitude']:.6f})\n")
                    f.write(f"    估计数量: {result.get('count', 1)} 个数据中心\n")
                    f.write(f"    来源: {result.get('source', '未知')}\n\n")
                
                f.write("技术说明:\n")
                f.write("-" * 30 + "\n")
                f.write("1. 聚合标记显示该区域有86个数据中心\n")
                f.write("2. 网站使用聚合算法隐藏了详细位置\n")
                f.write("3. 需要特定的API调用或参数才能获取完整数据\n")
                f.write("4. 建议使用浏览器开发工具监控网络请求\n")
            
            print(f"✅ 聚合分析报告已保存: {report_file}")
            
        except Exception as e:
            print(f"❌ 生成报告失败: {e}")

def main():
    """主函数"""
    print("🎯 上海市数据中心聚合数据解析器")
    print("🔍 专门解析地图聚合标记中的隐藏数据")
    
    crawler = ShanghaiClusterCrawler()
    
    try:
        # 运行综合爬取
        results = crawler.run_comprehensive_crawl()
        
        if results:
            print(f"\n🎉 聚合解析完成！")
            print(f"✅ 解析出 {len(results)} 个聚合点")
            
            total_estimated = sum(r.get('count', 1) for r in results)
            print(f"📊 估计总数据中心: {total_estimated} 个")
            
            # 保存结果
            crawler.save_results()
        else:
            print("❌ 未能解析出聚合数据")
            print("💡 建议：")
            print("   1. 检查网络连接")
            print("   2. 使用浏览器开发工具监控实际的API请求")
            print("   3. 可能需要模拟真实的用户交互")
            
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断任务")
    except Exception as e:
        print(f"❌ 执行过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
