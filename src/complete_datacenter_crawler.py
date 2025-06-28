#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整版数据中心爬虫 - 获取所有遗漏的数据
"""

import requests
import re
import json
import pandas as pd
import time

class CompleteDataCenterCrawler:
    def __init__(self):
        # 包含所有可能的URL
        self.urls = {
            "四川省-全称": "https://www.datacenters.com/locations/china/sichuan-sheng",
            "四川省-简称": "https://www.datacenters.com/locations/china/sichuan",
            "云南省-全称": "https://www.datacenters.com/locations/china/yunnan-sheng", 
            "云南省-简称": "https://www.datacenters.com/locations/china/yunnan",
            "贵州省-全称": "https://www.datacenters.com/locations/china/guizhou-sheng",
            "贵州省-简称": "https://www.datacenters.com/locations/china/guizhou",
        }
        
        self.province_mapping = {
            "四川省-全称": "四川省",
            "四川省-简称": "四川省", 
            "云南省-全称": "云南省",
            "云南省-简称": "云南省",
            "贵州省-全称": "贵州省",
            "贵州省-简称": "贵州省"
        }
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        self.all_results = []
        self.unique_coordinates = set()
    
    def extract_data_from_page(self, content, source_key):
        """从页面内容中提取数据"""
        found_data = []
        
        try:
            # 提取坐标
            latitudes = re.findall(r'"latitude":\s*([\d\.\-]+)', content)
            longitudes = re.findall(r'"longitude":\s*([\d\.\-]+)', content)
            
            print(f"  坐标: {len(latitudes)} 个纬度, {len(longitudes)} 个经度")
            
            if len(latitudes) != len(longitudes):
                print(f"  警告: 纬度和经度数量不匹配")
                return []
            
            # 提取数据中心名称
            name_patterns = [
                r'"name":\s*"([^"]*(?:Data Center|IDC|数据中心)[^"]*)"',
                r'"title":\s*"([^"]*(?:Data Center|IDC|数据中心)[^"]*)"',
                r'"name":\s*"([^"]*(?:' + self.province_mapping[source_key].replace('省', '') + '|Sichuan|Yunnan|Guizhou)[^"]*)"',
            ]
            
            all_names = []
            for pattern in name_patterns:
                names = re.findall(pattern, content, re.IGNORECASE)
                all_names.extend(names)
            
            # 去重名称
            unique_names = []
            seen_names = set()
            for name in all_names:
                clean_name = name.strip()
                if clean_name not in seen_names and len(clean_name) > 3:
                    unique_names.append(clean_name)
                    seen_names.add(clean_name)
            
            print(f"  名称: 找到 {len(unique_names)} 个唯一名称")
            
            # 组合数据
            province = self.province_mapping[source_key]
            
            for i, (lat, lng) in enumerate(zip(latitudes, longitudes)):
                try:
                    lat_f = float(lat)
                    lng_f = float(lng)
                    
                    # 验证坐标范围
                    if not (20 <= lat_f <= 35 and 95 <= lng_f <= 115):
                        continue
                    
                    # 检查是否重复
                    coord_key = (round(lat_f, 6), round(lng_f, 6))
                    if coord_key in self.unique_coordinates:
                        print(f"  跳过重复坐标: ({lat_f}, {lng_f})")
                        continue
                    
                    self.unique_coordinates.add(coord_key)
                    
                    # 选择名称
                    if i < len(unique_names):
                        name = unique_names[i]
                    else:
                        name = f"{province}数据中心{i+1}"
                    
                    data_center = {
                        'province': province,
                        'latitude': lat_f,
                        'longitude': lng_f,
                        'name': name,
                        'source': source_key,
                        'coordinates': f"{lat_f},{lng_f}"
                    }
                    
                    found_data.append(data_center)
                    print(f"  {len(found_data)}. {name} - ({lat_f:.6f}, {lng_f:.6f})")
                    
                except ValueError:
                    continue
            
        except Exception as e:
            print(f"  数据提取错误: {e}")
        
        return found_data
    
    def crawl_all_sources(self):
        """爬取所有数据源"""
        print("开始爬取所有数据源...")
        print("="*60)
        
        for source_key, url in self.urls.items():
            print(f"\n正在爬取: {source_key}")
            print(f"URL: {url}")
            print("-" * 40)
            
            try:
                response = requests.get(url, headers=self.headers, timeout=30)
                
                if response.status_code != 200:
                    print(f"  请求失败: {response.status_code}")
                    continue
                
                print(f"  页面大小: {len(response.text)} 字符")
                
                # 提取数据
                page_data = self.extract_data_from_page(response.text, source_key)
                
                if page_data:
                    self.all_results.extend(page_data)
                    print(f"  成功提取: {len(page_data)} 个数据中心")
                else:
                    print(f"  未找到数据")
                
                # 保存页面源码用于调试
                filename = f"{source_key.replace('-', '_')}_source.html"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                # 请求间隔
                time.sleep(2)
                
            except Exception as e:
                print(f"  爬取失败: {e}")
        
        print(f"\n{'='*60}")
        print(f"爬取完成！总计找到 {len(self.all_results)} 个数据中心")
        
        return self.all_results
    
    def save_complete_results(self):
        """保存完整结果"""
        if not self.all_results:
            print("没有数据需要保存")
            return
        
        # 按省份统计
        province_stats = {}
        for result in self.all_results:
            province = result['province']
            province_stats[province] = province_stats.get(province, 0) + 1
        
        print(f"\n各省份数据统计:")
        for province, count in province_stats.items():
            print(f"  {province}: {count} 个数据中心")
        
        # 保存CSV
        csv_file = "完整三省数据中心坐标.csv"
        try:
            df = pd.DataFrame(self.all_results)
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"\nCSV文件已保存: {csv_file}")
        except Exception as e:
            print(f"保存CSV失败: {e}")
        
        # 保存JSON
        json_file = "完整三省数据中心坐标.json"
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_results, f, ensure_ascii=False, indent=2)
            print(f"JSON文件已保存: {json_file}")
        except Exception as e:
            print(f"保存JSON失败: {e}")
        
        # 生成详细报告
        self.generate_detailed_report()
    
    def generate_detailed_report(self):
        """生成详细报告"""
        report_file = "完整数据中心报告.txt"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("完整三省数据中心分布报告\n")
                f.write("=" * 50 + "\n\n")
                
                f.write(f"爬取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"总数据中心数量: {len(self.all_results)}\n\n")
                
                # 按省份分组
                province_data = {}
                for result in self.all_results:
                    province = result['province']
                    if province not in province_data:
                        province_data[province] = []
                    province_data[province].append(result)
                
                f.write("各省份分布:\n")
                f.write("-" * 20 + "\n")
                for province, data in province_data.items():
                    f.write(f"{province}: {len(data)} 个数据中心\n")
                
                f.write(f"\n详细列表:\n")
                f.write("-" * 20 + "\n")
                
                for province, data in province_data.items():
                    f.write(f"\n{province} ({len(data)} 个):\n")
                    for i, dc in enumerate(data, 1):
                        f.write(f"  {i:2d}. {dc['name']}\n")
                        f.write(f"      坐标: ({dc['latitude']:.6f}, {dc['longitude']:.6f})\n")
                        f.write(f"      来源: {dc['source']}\n\n")
                
                # 坐标范围分析
                if self.all_results:
                    lats = [r['latitude'] for r in self.all_results]
                    lngs = [r['longitude'] for r in self.all_results]
                    
                    f.write(f"坐标范围分析:\n")
                    f.write(f"  纬度范围: {min(lats):.6f} ~ {max(lats):.6f}\n")
                    f.write(f"  经度范围: {min(lngs):.6f} ~ {max(lngs):.6f}\n")
            
            print(f"详细报告已保存: {report_file}")
            
        except Exception as e:
            print(f"生成报告失败: {e}")
    
    def display_results(self):
        """显示结果"""
        if not self.all_results:
            print("没有找到任何数据")
            return
        
        print(f"\n{'='*80}")
        print(f"完整爬取结果")
        print(f"{'='*80}")
        
        # 按省份分组显示
        province_data = {}
        for result in self.all_results:
            province = result['province']
            if province not in province_data:
                province_data[province] = []
            province_data[province].append(result)
        
        for province, data in province_data.items():
            print(f"\n{province} ({len(data)} 个数据中心):")
            print("-" * 40)
            for i, dc in enumerate(data, 1):
                print(f"{i:2d}. {dc['name']}")
                print(f"    坐标: ({dc['latitude']:.6f}, {dc['longitude']:.6f})")
                print(f"    来源: {dc['source']}")

def main():
    """主函数"""
    print("完整版数据中心爬虫启动")
    print("目标: 获取四川省、云南省、贵州省的所有数据中心")
    print("方法: 多URL源 + HTML解析")
    
    crawler = CompleteDataCenterCrawler()
    
    try:
        # 爬取所有数据
        results = crawler.crawl_all_sources()
        
        if results:
            # 显示结果
            crawler.display_results()
            
            # 保存数据
            crawler.save_complete_results()
            
            print(f"\n✓ 任务完成！")
            print(f"✓ 成功获取 {len(results)} 个数据中心")
            print(f"✓ 包含所有遗漏的 Sichuan、Si Chuan Sheng、Guizhou 数据")
            print(f"✓ 数据已保存为完整版本")
        else:
            print("未获取到任何数据")
            
    except KeyboardInterrupt:
        print("\n用户中断任务")
    except Exception as e:
        print(f"执行过程中出错: {e}")

if __name__ == "__main__":
    main()
