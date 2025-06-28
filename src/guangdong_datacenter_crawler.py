#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
广东省数据中心爬虫 - 专门爬取广东省数据中心分布信息
"""

import requests
import re
import json
import pandas as pd
import time
import os
from datetime import datetime

class GuangdongDataCenterCrawler:
    def __init__(self):
        # 广东省的所有可能URL变体
        self.urls = {
            # 广东省的各种英文拼写变体
            "广东省-guangdong-sheng": "https://www.datacenters.com/locations/china/guangdong-sheng",
            "广东省-guangdong": "https://www.datacenters.com/locations/china/guangdong",
            "广东省-guang-dong-sheng": "https://www.datacenters.com/locations/china/guang-dong-sheng",
            "广东省-guang-dong": "https://www.datacenters.com/locations/china/guang-dong",
            "广东省-kwantung": "https://www.datacenters.com/locations/china/kwantung",
            "广东省-canton": "https://www.datacenters.com/locations/china/canton",
            
            # 主要城市
            "深圳-shenzhen": "https://www.datacenters.com/locations/china/shenzhen",
            "广州-guangzhou": "https://www.datacenters.com/locations/china/guangzhou",
            "东莞-dongguan": "https://www.datacenters.com/locations/china/dongguan",
            "佛山-foshan": "https://www.datacenters.com/locations/china/foshan",
            "珠海-zhuhai": "https://www.datacenters.com/locations/china/zhuhai",
            "中山-zhongshan": "https://www.datacenters.com/locations/china/zhongshan",
            "惠州-huizhou": "https://www.datacenters.com/locations/china/huizhou",
        }
        
        # URL与省份/城市的映射
        self.location_mapping = {
            "广东省-guangdong-sheng": "广东省",
            "广东省-guangdong": "广东省",
            "广东省-guang-dong-sheng": "广东省",
            "广东省-guang-dong": "广东省",
            "广东省-kwantung": "广东省",
            "广东省-canton": "广东省",
            "深圳-shenzhen": "深圳市",
            "广州-guangzhou": "广州市",
            "东莞-dongguan": "东莞市",
            "佛山-foshan": "佛山市",
            "珠海-zhuhai": "珠海市",
            "中山-zhongshan": "中山市",
            "惠州-huizhou": "惠州市",
        }
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        self.all_results = []
        self.unique_coordinates = set()
        
        # 创建输出目录
        self.create_output_directories()
    
    def create_output_directories(self):
        """创建输出目录结构"""
        directories = [
            "data/guangdong",
            "reports/guangdong", 
            "html_sources/guangdong"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def extract_data_from_page(self, content, source_key):
        """从页面内容中提取数据中心信息"""
        found_data = []
        
        try:
            print(f"  正在解析页面内容...")
            
            # 提取坐标信息
            latitude_patterns = [
                r'"latitude":\s*([\d\.\-]+)',
                r'"lat":\s*([\d\.\-]+)',
                r'latitude:\s*([\d\.\-]+)',
                r'lat:\s*([\d\.\-]+)'
            ]
            
            longitude_patterns = [
                r'"longitude":\s*([\d\.\-]+)',
                r'"lng":\s*([\d\.\-]+)',
                r'"lon":\s*([\d\.\-]+)',
                r'longitude:\s*([\d\.\-]+)',
                r'lng:\s*([\d\.\-]+)',
                r'lon:\s*([\d\.\-]+)'
            ]
            
            # 收集所有坐标
            latitudes = []
            longitudes = []
            
            for pattern in latitude_patterns:
                latitudes.extend(re.findall(pattern, content))
            
            for pattern in longitude_patterns:
                longitudes.extend(re.findall(pattern, content))
            
            # 去重并转换为浮点数
            latitudes = list(set([float(lat) for lat in latitudes if self.is_valid_latitude(lat)]))
            longitudes = list(set([float(lng) for lng in longitudes if self.is_valid_longitude(lng)]))
            
            print(f"  找到坐标: {len(latitudes)} 个纬度, {len(longitudes)} 个经度")
            
            # 提取数据中心名称
            name_patterns = [
                r'"name":\s*"([^"]*(?:Data Center|IDC|数据中心|机房|云计算)[^"]*)"',
                r'"title":\s*"([^"]*(?:Data Center|IDC|数据中心|机房|云计算)[^"]*)"',
                r'"facility_name":\s*"([^"]*)"',
                r'<h[1-6][^>]*>([^<]*(?:Data Center|IDC|数据中心|机房|云计算)[^<]*)</h[1-6]>',
                # 广东相关的特定模式
                r'"name":\s*"([^"]*(?:广东|深圳|广州|东莞|佛山|珠海|中山|惠州|Guangdong|Shenzhen|Guangzhou)[^"]*)"',
                r'"title":\s*"([^"]*(?:广东|深圳|广州|东莞|佛山|珠海|中山|惠州|Guangdong|Shenzhen|Guangzhou)[^"]*)"',
            ]
            
            all_names = []
            for pattern in name_patterns:
                names = re.findall(pattern, content, re.IGNORECASE)
                all_names.extend(names)
            
            # 清理和去重名称
            unique_names = self.clean_and_dedupe_names(all_names)
            print(f"  找到名称: {len(unique_names)} 个唯一名称")
            
            # 组合坐标数据
            location = self.location_mapping[source_key]
            
            # 创建坐标对
            coordinates_pairs = []
            
            # 如果纬度和经度数量相等，直接配对
            if len(latitudes) == len(longitudes):
                coordinates_pairs = list(zip(latitudes, longitudes))
            else:
                # 如果数量不等，尝试智能匹配
                coordinates_pairs = self.smart_coordinate_matching(latitudes, longitudes)
            
            # 创建数据中心记录
            for i, (lat, lng) in enumerate(coordinates_pairs):
                # 验证坐标是否在广东省范围内
                if not self.is_in_guangdong_region(lat, lng):
                    print(f"  跳过非广东省坐标: ({lat}, {lng})")
                    continue
                
                # 检查是否重复
                coord_key = (round(lat, 6), round(lng, 6))
                if coord_key in self.unique_coordinates:
                    print(f"  跳过重复坐标: ({lat}, {lng})")
                    continue
                
                self.unique_coordinates.add(coord_key)
                
                # 选择名称
                if i < len(unique_names):
                    name = unique_names[i]
                else:
                    name = f"{location}数据中心{i+1}"
                
                data_center = {
                    'province': '广东省',
                    'city': location,
                    'latitude': lat,
                    'longitude': lng,
                    'name': name,
                    'source': source_key,
                    'coordinates': f"{lat},{lng}",
                    'index': len(self.all_results) + len(found_data) + 1,
                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                found_data.append(data_center)
                print(f"  {len(found_data)}. {name} - ({lat:.6f}, {lng:.6f})")
        
        except Exception as e:
            print(f"  数据提取错误: {e}")
        
        return found_data
    
    def is_valid_latitude(self, lat_str):
        """验证纬度是否有效"""
        try:
            lat = float(lat_str)
            return 20.0 <= lat <= 25.5  # 广东省纬度范围
        except:
            return False
    
    def is_valid_longitude(self, lng_str):
        """验证经度是否有效"""
        try:
            lng = float(lng_str)
            return 109.0 <= lng <= 117.5  # 广东省经度范围
        except:
            return False
    
    def is_in_guangdong_region(self, lat, lng):
        """检查坐标是否在广东省范围内"""
        # 广东省大致的地理边界
        return (20.0 <= lat <= 25.5) and (109.0 <= lng <= 117.5)
    
    def clean_and_dedupe_names(self, names):
        """清理和去重名称"""
        unique_names = []
        seen_names = set()
        
        for name in names:
            clean_name = name.strip()
            # 过滤掉太短或太长的名称
            if 3 <= len(clean_name) <= 100:
                # 转换为小写进行比较，但保持原始大小写
                name_lower = clean_name.lower()
                if name_lower not in seen_names:
                    unique_names.append(clean_name)
                    seen_names.add(name_lower)
        
        return unique_names
    
    def smart_coordinate_matching(self, latitudes, longitudes):
        """智能坐标匹配"""
        coordinates_pairs = []
        
        # 如果其中一个列表为空，返回空列表
        if not latitudes or not longitudes:
            return coordinates_pairs
        
        # 使用较短的列表长度
        min_length = min(len(latitudes), len(longitudes))
        
        for i in range(min_length):
            coordinates_pairs.append((latitudes[i], longitudes[i]))
        
        return coordinates_pairs
    
    def crawl_all_sources(self):
        """爬取所有数据源"""
        print("🌟 广东省数据中心爬虫启动")
        print("🎯 目标：爬取广东省及主要城市的数据中心分布信息")
        print("="*70)
        
        success_count = 0
        failed_count = 0
        
        for source_key, url in self.urls.items():
            print(f"\n🔍 正在爬取: {source_key}")
            print(f"📍 URL: {url}")
            print("-" * 50)
            
            try:
                response = requests.get(url, headers=self.headers, timeout=30)
                
                if response.status_code != 200:
                    print(f"  ❌ 请求失败: HTTP {response.status_code}")
                    failed_count += 1
                    continue
                
                print(f"  ✅ 请求成功，页面大小: {len(response.text)} 字符")
                
                # 提取数据
                page_data = self.extract_data_from_page(response.text, source_key)
                
                if page_data:
                    self.all_results.extend(page_data)
                    print(f"  🎉 成功提取: {len(page_data)} 个数据中心")
                    success_count += 1
                else:
                    print(f"  ⚠️ 未找到数据")
                
                # 保存页面源码用于调试
                filename = f"html_sources/guangdong/{source_key.replace('-', '_')}_source.html"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"  💾 页面源码已保存: {filename}")
                
                # 请求间隔，避免被封IP
                time.sleep(3)
                
            except requests.exceptions.Timeout:
                print(f"  ⏱️ 请求超时")
                failed_count += 1
            except requests.exceptions.RequestException as e:
                print(f"  ❌ 网络错误: {e}")
                failed_count += 1
            except Exception as e:
                print(f"  ❌ 未知错误: {e}")
                failed_count += 1
        
        print(f"\n{'='*70}")
        print(f"📊 爬取统计:")
        print(f"  ✅ 成功: {success_count} 个数据源")
        print(f"  ❌ 失败: {failed_count} 个数据源")
        print(f"  🎯 总计找到: {len(self.all_results)} 个数据中心")
        
        return self.all_results
    
    def save_results(self):
        """保存爬取结果"""
        if not self.all_results:
            print("❌ 没有数据需要保存")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 按城市统计
        city_stats = {}
        for result in self.all_results:
            city = result['city']
            city_stats[city] = city_stats.get(city, 0) + 1
        
        print(f"\n📊 数据统计:")
        total = sum(city_stats.values())
        for city, count in city_stats.items():
            print(f"  {city}: {count} 个数据中心")
        print(f"  📍 总计: {total} 个数据中心")
        
        # 保存CSV文件
        csv_file = f"data/guangdong/广东省数据中心坐标_{timestamp}.csv"
        try:
            df = pd.DataFrame(self.all_results)
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"✅ CSV文件已保存: {csv_file}")
        except Exception as e:
            print(f"❌ 保存CSV失败: {e}")
        
        # 保存JSON文件
        json_file = f"data/guangdong/广东省数据中心坐标_{timestamp}.json"
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_results, f, ensure_ascii=False, indent=2)
            print(f"✅ JSON文件已保存: {json_file}")
        except Exception as e:
            print(f"❌ 保存JSON失败: {e}")
        
        # 生成报告
        self.generate_report(timestamp)
    
    def generate_report(self, timestamp):
        """生成详细报告"""
        report_file = f"reports/guangdong/广东省数据中心分布报告_{timestamp}.txt"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("广东省数据中心分布分析报告\n")
                f.write("=" * 60 + "\n\n")
                
                f.write(f"爬取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"总数据中心数量: {len(self.all_results)}\n\n")
                
                # 数据源统计
                f.write("数据源统计:\n")
                f.write("-" * 30 + "\n")
                source_stats = {}
                for result in self.all_results:
                    source = result['source']
                    source_stats[source] = source_stats.get(source, 0) + 1
                
                for source, count in source_stats.items():
                    f.write(f"{source}: {count} 个数据中心\n")
                
                # 按城市分组
                city_data = {}
                for result in self.all_results:
                    city = result['city']
                    if city not in city_data:
                        city_data[city] = []
                    city_data[city].append(result)
                
                f.write(f"\n城市分布统计:\n")
                f.write("-" * 20 + "\n")
                for city, data in city_data.items():
                    f.write(f"{city}: {len(data)} 个数据中心\n")
                
                f.write(f"\n详细列表:\n")
                f.write("-" * 20 + "\n")
                
                for city, data in city_data.items():
                    f.write(f"\n{city} ({len(data)} 个):\n")
                    for i, dc in enumerate(data, 1):
                        f.write(f"  {i:2d}. {dc['name']}\n")
                        f.write(f"      坐标: ({dc['latitude']:.6f}, {dc['longitude']:.6f})\n")
                        f.write(f"      来源: {dc['source']}\n")
                        f.write(f"      爬取时间: {dc['crawl_time']}\n\n")
                
                # 地理分布分析
                if self.all_results:
                    lats = [r['latitude'] for r in self.all_results]
                    lngs = [r['longitude'] for r in self.all_results]
                    
                    f.write(f"地理分布分析:\n")
                    f.write(f"-" * 20 + "\n")
                    f.write(f"纬度范围: {min(lats):.6f} ~ {max(lats):.6f}\n")
                    f.write(f"经度范围: {min(lngs):.6f} ~ {max(lngs):.6f}\n")
                    f.write(f"中心点: ({sum(lats)/len(lats):.6f}, {sum(lngs)/len(lngs):.6f})\n")
                
                # 技术说明
                f.write(f"\n技术说明:\n")
                f.write(f"-" * 20 + "\n")
                f.write(f"1. 爬取范围：广东省及其主要城市\n")
                f.write(f"2. 坐标验证：仅保留广东省地理范围内的坐标\n")
                f.write(f"3. 去重策略：基于坐标精度到小数点后6位\n")
                f.write(f"4. 数据来源：datacenters.com网站\n")
                f.write(f"5. 爬取策略：多URL变体，包含省级和市级查询\n")
            
            print(f"✅ 详细报告已保存: {report_file}")
            
        except Exception as e:
            print(f"❌ 生成报告失败: {e}")
    
    def display_results(self):
        """显示爬取结果"""
        if not self.all_results:
            print("❌ 没有找到任何数据")
            return
        
        print(f"\n{'='*80}")
        print(f"🎯 广东省数据中心爬取结果")
        print(f"{'='*80}")
        
        # 按城市分组显示
        city_data = {}
        for result in self.all_results:
            city = result['city']
            if city not in city_data:
                city_data[city] = []
            city_data[city].append(result)
        
        for city, data in city_data.items():
            print(f"\n📍 {city} ({len(data)} 个数据中心):")
            print("-" * 50)
            for i, dc in enumerate(data, 1):
                print(f"{i:2d}. {dc['name']}")
                print(f"    🗺️  坐标: ({dc['latitude']:.6f}, {dc['longitude']:.6f})")
                print(f"    📊 来源: {dc['source']}")
                print(f"    ⏰ 时间: {dc['crawl_time']}")
                print()

def main():
    """主函数"""
    print("🚀 广东省数据中心爬虫启动")
    print("🎯 专业爬取广东省数据中心分布信息")
    print("📍 包含：深圳、广州、东莞、佛山、珠海、中山、惠州等主要城市")
    
    crawler = GuangdongDataCenterCrawler()
    
    try:
        # 开始爬取
        results = crawler.crawl_all_sources()
        
        if results:
            # 显示结果
            crawler.display_results()
            
            # 保存数据
            crawler.save_results()
            
            print(f"\n🎉 任务完成！")
            print(f"✅ 成功获取 {len(results)} 个广东省数据中心")
            print(f"✅ 涵盖广东省主要城市")
            print(f"✅ 数据已保存到 data/guangdong/ 目录")
            print(f"✅ 报告已生成到 reports/guangdong/ 目录")
            
            print(f"\n📁 生成的文件:")
            print(f"  - CSV格式数据文件")
            print(f"  - JSON格式数据文件") 
            print(f"  - 详细分析报告")
            print(f"  - HTML源码文件（用于调试）")
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
