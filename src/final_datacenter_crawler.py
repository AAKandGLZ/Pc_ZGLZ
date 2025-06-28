#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于HTML解析的数据中心爬虫
通过分析发现网站将坐标数据直接嵌入在HTML中，使用正则表达式提取更加可靠
"""

import requests
import re
import json
import pandas as pd
import time

class HTMLDataCenterCrawler:
    def __init__(self):
        self.provinces = {
            "四川省": "https://www.datacenters.com/locations/china/sichuan-sheng",
            "云南省": "https://www.datacenters.com/locations/china/yunnan-sheng", 
            "贵州省": "https://www.datacenters.com/locations/china/guizhou-sheng"
        }
        self.results = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def extract_coordinates_and_names(self, html_content, province_name):
        """从HTML内容中提取坐标和名称"""
        data_centers = []
        
        try:
            # 提取纬度和经度
            latitudes = re.findall(r'"latitude":\s*([\d\.\-]+)', html_content)
            longitudes = re.findall(r'"longitude":\s*([\d\.\-]+)', html_content)
            
            print(f"  找到 {len(latitudes)} 个纬度, {len(longitudes)} 个经度")
            
            if len(latitudes) != len(longitudes):
                print("  警告: 纬度和经度数量不匹配")
                return []
            
            # 提取数据中心名称
            name_patterns = [
                r'"name":\s*"([^"]*(?:Data Center|IDC|数据中心)[^"]*)"',
                r'"title":\s*"([^"]*(?:Data Center|IDC|数据中心)[^"]*)"',
                r'"name":\s*"([^"]*(?:' + province_name.replace('省', '') + ')[^"]*)"'
            ]
            
            all_names = []
            for pattern in name_patterns:
                names = re.findall(pattern, html_content, re.IGNORECASE)
                all_names.extend(names)
            
            print(f"  找到 {len(all_names)} 个可能的名称")
            
            # 提取地址信息
            address_patterns = [
                r'"address":\s*"([^"]+)"',
                r'"location":\s*"([^"]+)"',
                r'"description":\s*"([^"]*(?:China|' + province_name.replace('省', '') + ')[^"]*)"'
            ]
            
            all_addresses = []
            for pattern in address_patterns:
                addresses = re.findall(pattern, html_content, re.IGNORECASE)
                all_addresses.extend(addresses)
            
            # 组合数据
            for i, (lat, lng) in enumerate(zip(latitudes, longitudes)):
                # 选择合适的名称
                if i < len(all_names) and all_names[i]:
                    name = all_names[i]
                else:
                    name = f"{province_name}数据中心{i+1}"
                
                # 选择合适的地址
                if i < len(all_addresses) and all_addresses[i]:
                    address = all_addresses[i]
                else:
                    address = f"{province_name}地区"
                
                data_center = {
                    'index': i + 1,
                    'province': province_name,
                    'latitude': float(lat),
                    'longitude': float(lng),
                    'name': name,
                    'address': address,
                    'coordinates': f"{lat},{lng}"
                }
                
                data_centers.append(data_center)
                print(f"  {i+1}. {name} - ({lat}, {lng})")
            
        except Exception as e:
            print(f"  数据提取错误: {e}")
        
        return data_centers
    
    def crawl_province(self, province_name, url):
        """爬取单个省份的数据"""
        print(f"\n{'='*60}")
        print(f"正在爬取: {province_name}")
        print(f"URL: {url}")
        print(f"{'='*60}")
        
        try:
            # 发送HTTP请求
            print("发送HTTP请求...")
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code != 200:
                print(f"请求失败，状态码: {response.status_code}")
                return []
            
            print(f"请求成功，页面大小: {len(response.text)} 字符")
            
            # 提取数据
            province_data = self.extract_coordinates_and_names(response.text, province_name)
            
            if province_data:
                print(f"成功提取 {len(province_data)} 个数据中心")
                
                # 保存省份的HTML用于调试
                debug_file = f"e:\\空间统计分析\\爬虫\\{province_name}_source.html"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"页面源码已保存到: {debug_file}")
            else:
                print("未找到任何数据中心")
            
            return province_data
            
        except Exception as e:
            print(f"爬取 {province_name} 失败: {e}")
            return []
    
    def crawl_all_provinces(self):
        """爬取所有省份"""
        print("开始爬取所有省份的数据中心信息...")
        print("方法: HTML解析 + 正则表达式")
        
        for province, url in self.provinces.items():
            try:
                province_data = self.crawl_province(province, url)
                self.results.extend(province_data)
                
                # 省份间休息
                if province != list(self.provinces.keys())[-1]:
                    print("等待3秒后继续...")
                    time.sleep(3)
                
            except Exception as e:
                print(f"处理 {province} 时出错: {e}")
                continue
        
        print(f"\n所有省份爬取完成，总计找到 {len(self.results)} 个数据中心")
        return self.results
    
    def save_results(self):
        """保存结果到文件"""
        if not self.results:
            print("没有数据需要保存")
            return
        
        # 保存为CSV
        csv_file = "e:\\空间统计分析\\爬虫\\三省数据中心坐标.csv"
        try:
            df = pd.DataFrame(self.results)
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"CSV文件已保存: {csv_file}")
        except Exception as e:
            print(f"保存CSV失败: {e}")
        
        # 保存为JSON
        json_file = "e:\\空间统计分析\\爬虫\\三省数据中心坐标.json"
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            print(f"JSON文件已保存: {json_file}")
        except Exception as e:
            print(f"保存JSON失败: {e}")
        
        # 生成统计报告
        self.generate_report()
    
    def generate_report(self):
        """生成统计报告"""
        report_file = "e:\\空间统计分析\\爬虫\\数据中心统计报告.txt"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("三省数据中心分布统计报告\n")
                f.write("=" * 40 + "\n\n")
                
                # 总体统计
                f.write(f"总数据中心数量: {len(self.results)}\n")
                f.write(f"爬取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # 各省份统计
                province_stats = {}
                for result in self.results:
                    province = result['province']
                    if province not in province_stats:
                        province_stats[province] = []
                    province_stats[province].append(result)
                
                f.write("各省份分布:\n")
                f.write("-" * 20 + "\n")
                for province, data in province_stats.items():
                    f.write(f"{province}: {len(data)} 个数据中心\n")
                
                f.write("\n详细列表:\n")
                f.write("-" * 20 + "\n")
                
                for province, data in province_stats.items():
                    f.write(f"\n{province}:\n")
                    for i, dc in enumerate(data, 1):
                        f.write(f"  {i}. {dc['name']}\n")
                        f.write(f"     坐标: ({dc['latitude']:.6f}, {dc['longitude']:.6f})\n")
                        f.write(f"     地址: {dc['address']}\n\n")
            
            print(f"统计报告已保存: {report_file}")
            
        except Exception as e:
            print(f"生成报告失败: {e}")
    
    def display_summary(self):
        """显示结果摘要"""
        if not self.results:
            print("没有找到任何数据")
            return
        
        print(f"\n{'='*80}")
        print(f"爬取结果摘要")
        print(f"{'='*80}")
        
        # 按省份统计
        province_count = {}
        for result in self.results:
            province = result['province']
            province_count[province] = province_count.get(province, 0) + 1
        
        print(f"总数据中心数量: {len(self.results)}")
        print("\n各省份分布:")
        for province, count in province_count.items():
            print(f"  {province}: {count} 个")
        
        print(f"\n坐标范围分析:")
        if self.results:
            lats = [r['latitude'] for r in self.results]
            lngs = [r['longitude'] for r in self.results]
            print(f"  纬度范围: {min(lats):.4f} ~ {max(lats):.4f}")
            print(f"  经度范围: {min(lngs):.4f} ~ {max(lngs):.4f}")
        
        print(f"\n数据中心列表:")
        print("-" * 80)
        for i, result in enumerate(self.results, 1):
            print(f"{i:2d}. {result['province']} - {result['name']}")
            print(f"    坐标: ({result['latitude']:.6f}, {result['longitude']:.6f})")
            print(f"    地址: {result['address']}")
            print("-" * 40)

def main():
    """主函数"""
    print("=" * 80)
    print("数据中心坐标爬虫 - HTML解析版")
    print("目标: 四川省、云南省、贵州省")
    print("=" * 80)
    
    crawler = HTMLDataCenterCrawler()
    
    try:
        # 执行爬取
        results = crawler.crawl_all_provinces()
        
        # 显示结果
        crawler.display_summary()
        
        # 保存数据
        crawler.save_results()
        
        if results:
            print(f"\n✓ 爬取任务完成！")
            print(f"✓ 成功获取 {len(results)} 个数据中心的坐标信息")
            print(f"✓ 数据已保存为CSV、JSON格式")
            print(f"✓ 统计报告已生成")
            print(f"\n可用于空间统计分析的文件:")
            print(f"  - 三省数据中心坐标.csv")
            print(f"  - 三省数据中心坐标.json")
            print(f"  - 数据中心统计报告.txt")
        else:
            print(f"\n✗ 未获取到任何数据")
            
    except KeyboardInterrupt:
        print(f"\n\n用户中断了爬取任务")
    except Exception as e:
        print(f"\n执行过程中发生错误: {e}")

if __name__ == "__main__":
    main()
