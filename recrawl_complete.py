#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比分析和重新爬取脚本
"""

import json
import requests
import re
import pandas as pd
import time

def compare_results():
    """对比之前的结果和详细检查结果"""
    
    print("对比分析之前的结果和详细检查结果...")
    print("="*60)
    
    # 读取之前的完整结果
    try:
        with open('最终完整三省数据中心坐标.json', 'r', encoding='utf-8') as f:
            previous_data = json.load(f)
    except:
        print("未找到之前的结果文件")
        return
    
    # 读取详细检查结果
    try:
        with open('详细检查结果汇总.json', 'r', encoding='utf-8') as f:
            detailed_data = json.load(f)
    except:
        print("未找到详细检查结果文件")
        return
    
    print('之前结果中的四川省坐标:')
    previous_sichuan = [item for item in previous_data if item['province'] == '四川省']
    print(f'数量: {len(previous_sichuan)}')
    
    previous_coords = set()
    for item in previous_sichuan:
        coord = (round(item['latitude'], 6), round(item['longitude'], 6))
        previous_coords.add(coord)
    
    print(f'\n详细检查发现的坐标:')
    detailed_coords = set()
    for coord in detailed_data['unique_coordinates']:
        coord_tuple = (round(coord['latitude'], 6), round(coord['longitude'], 6))
        detailed_coords.add(coord_tuple)
    
    print(f'\n对比分析:')
    print(f'之前结果: {len(previous_coords)} 个唯一坐标')
    print(f'详细检查: {len(detailed_coords)} 个唯一坐标')
    
    # 找出遗漏的坐标
    missing = detailed_coords - previous_coords
    found_extra = previous_coords - detailed_coords
    
    if missing:
        print(f'\n❌ 遗漏的坐标 ({len(missing)} 个):')
        for coord in missing:
            print(f'  {coord}')
    else:
        print(f'\n✅ 没有遗漏的坐标')
    
    if found_extra:
        print(f'\n➕ 之前多找到的坐标 ({len(found_extra)} 个):')
        for coord in found_extra:
            print(f'  {coord}')
    
    return len(missing) > 0

class FinalCompleteCrawler:
    """最终完整爬虫类"""
    
    def __init__(self):
        self.urls = {
            # 四川省的所有变体
            "四川省-sichuan-sheng": "https://www.datacenters.com/locations/china/sichuan-sheng",
            "四川省-si-chuan-sheng": "https://www.datacenters.com/locations/china/si-chuan-sheng",
            "四川省-sichuan": "https://www.datacenters.com/locations/china/sichuan",
            
            # 云南省
            "云南省-yunnan-sheng": "https://www.datacenters.com/locations/china/yunnan-sheng", 
            "云南省-yunnan": "https://www.datacenters.com/locations/china/yunnan",
            
            # 贵州省
            "贵州省-guizhou-sheng": "https://www.datacenters.com/locations/china/guizhou-sheng",
            "贵州省-guizhou": "https://www.datacenters.com/locations/china/guizhou",
        }
        
        self.province_mapping = {
            "四川省-sichuan-sheng": "四川省",
            "四川省-si-chuan-sheng": "四川省",
            "四川省-sichuan": "四川省",
            "云南省-yunnan-sheng": "云南省",
            "云南省-yunnan": "云南省",
            "贵州省-guizhou-sheng": "贵州省",
            "贵州省-guizhou": "贵州省"
        }
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        self.all_results = []
        self.unique_coordinates = set()
    
    def extract_comprehensive_data(self, content, source_key):
        """全面提取页面数据"""
        found_data = []
        
        try:
            # 提取坐标 - 使用多种模式
            coordinate_patterns = [
                (r'"latitude":\s*([\d\.\-]+)', r'"longitude":\s*([\d\.\-]+)'),
                (r'"lat":\s*([\d\.\-]+)', r'"lng":\s*([\d\.\-]+)'),
            ]
            
            all_coords = []
            
            for lat_pattern, lng_pattern in coordinate_patterns:
                lats = re.findall(lat_pattern, content)
                lngs = re.findall(lng_pattern, content)
                
                if lats and lngs and len(lats) == len(lngs):
                    for lat, lng in zip(lats, lngs):
                        try:
                            lat_f = float(lat)
                            lng_f = float(lng)
                            if 20 <= lat_f <= 35 and 95 <= lng_f <= 115:
                                all_coords.append((lat_f, lng_f))
                        except:
                            continue
            
            print(f"  原始坐标: {len(all_coords)} 个")
            
            # 去重坐标
            unique_coords = []
            seen_coords = set()
            for lat, lng in all_coords:
                coord_key = (round(lat, 6), round(lng, 6))
                if coord_key not in seen_coords:
                    seen_coords.add(coord_key)
                    unique_coords.append((lat, lng))
            
            print(f"  去重后坐标: {len(unique_coords)} 个")
            
            # 提取名称 - 使用更全面的模式
            name_patterns = [
                r'"name":\s*"([^"]*(?:Data Center|IDC|数据中心)[^"]*)"',
                r'"title":\s*"([^"]*(?:Data Center|IDC|数据中心)[^"]*)"',
                r'"name":\s*"([^"]*(?:' + self.province_mapping[source_key].replace('省', '') + '|Sichuan|Yunnan|Guizhou|Chengdu|CTU|GDS|Telecom|Tianfu|Mianyang|Yibin|Ziyang|Neijiang|Dazhou|Panzhihua|Nanchong|Leshan|Guangyuan|Deyang)[^"]*)"',
                r'"displayName":\s*"([^"]+)"',
                r'"label":\s*"([^"]+)"',
            ]
            
            all_names = []
            for pattern in name_patterns:
                names = re.findall(pattern, content, re.IGNORECASE)
                all_names.extend(names)
            
            # 过滤和清理名称
            filtered_names = []
            seen_names = set()
            for name in all_names:
                clean_name = name.strip()
                if (len(clean_name) > 3 and 
                    len(clean_name) < 200 and 
                    clean_name not in seen_names):
                    
                    # 检查是否是有效的数据中心名称
                    keywords = ['data center', 'idc', '数据中心', 'center', 'chengdu', 'sichuan', 
                               'telecom', 'gds', 'ctu', 'tianfu', 'mianyang', 'yibin', 'ziyang',
                               'neijiang', 'dazhou', 'panzhihua', 'nanchong', 'leshan', 'guangyuan', 'deyang']
                    
                    if any(keyword in clean_name.lower() for keyword in keywords):
                        filtered_names.append(clean_name)
                        seen_names.add(clean_name)
            
            print(f"  找到名称: {len(filtered_names)} 个")
            
            # 组合数据
            province = self.province_mapping[source_key]
            
            for i, (lat, lng) in enumerate(unique_coords):
                # 检查全局重复
                global_coord_key = (round(lat, 6), round(lng, 6))
                if global_coord_key in self.unique_coordinates:
                    print(f"  跳过重复坐标: ({lat:.6f}, {lng:.6f})")
                    continue
                
                self.unique_coordinates.add(global_coord_key)
                
                # 选择名称
                if i < len(filtered_names):
                    name = filtered_names[i]
                else:
                    name = f"{province}数据中心{i+1}"
                
                data_center = {
                    'province': province,
                    'latitude': lat,
                    'longitude': lng,
                    'name': name,
                    'source': source_key,
                    'coordinates': f"{lat},{lng}",
                    'index': len(self.all_results) + len(found_data) + 1
                }
                
                found_data.append(data_center)
                print(f"  ✅ {len(found_data)}. {name} - ({lat:.6f}, {lng:.6f})")
            
        except Exception as e:
            print(f"  ❌ 数据提取错误: {e}")
        
        return found_data
    
    def crawl_all_sources(self):
        """重新爬取所有数据源"""
        print("\n" + "="*80)
        print("🔄 重新爬取所有数据源")
        print("="*80)
        
        for source_key, url in self.urls.items():
            print(f"\n🔍 正在爬取: {source_key}")
            print(f"📍 URL: {url}")
            print("-" * 60)
            
            try:
                response = requests.get(url, headers=self.headers, timeout=30)
                
                if response.status_code != 200:
                    print(f"  ❌ 请求失败: {response.status_code}")
                    continue
                
                print(f"  📄 页面大小: {len(response.text)} 字符")
                
                # 全面提取数据
                page_data = self.extract_comprehensive_data(response.text, source_key)
                
                if page_data:
                    self.all_results.extend(page_data)
                    print(f"  ✅ 成功提取: {len(page_data)} 个数据中心")
                else:
                    print(f"  ⚠️ 未找到数据")
                
                # 请求间隔
                time.sleep(2)
                
            except Exception as e:
                print(f"  ❌ 爬取失败: {e}")
        
        print(f"\n" + "="*80)
        print(f"🎉 重新爬取完成！总计找到 {len(self.all_results)} 个数据中心")
        
        return self.all_results
    
    def save_final_results(self):
        """保存最终结果"""
        if not self.all_results:
            print("❌ 没有数据需要保存")
            return
        
        # 按省份统计
        province_stats = {}
        for result in self.all_results:
            province = result['province']
            province_stats[province] = province_stats.get(province, 0) + 1
        
        print(f"\n📊 最终统计:")
        total = sum(province_stats.values())
        for province, count in province_stats.items():
            print(f"  📍 {province}: {count} 个数据中心")
        print(f"  🎯 总计: {total} 个数据中心")
        
        # 保存CSV
        csv_file = "重新爬取完整三省数据中心坐标.csv"
        try:
            df = pd.DataFrame(self.all_results)
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"\n✅ CSV文件已保存: {csv_file}")
        except Exception as e:
            print(f"❌ 保存CSV失败: {e}")
        
        # 保存JSON
        json_file = "重新爬取完整三省数据中心坐标.json"
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_results, f, ensure_ascii=False, indent=2)
            print(f"✅ JSON文件已保存: {json_file}")
        except Exception as e:
            print(f"❌ 保存JSON失败: {e}")
        
        # 生成报告
        self.generate_final_report(province_stats)
    
    def generate_final_report(self, province_stats):
        """生成最终报告"""
        report_file = "重新爬取数据中心报告.txt"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("重新爬取完整三省数据中心报告\n")
                f.write("=" * 70 + "\n\n")
                
                f.write(f"爬取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"总数据中心数量: {len(self.all_results)}\n\n")
                
                # 数据源统计
                source_stats = {}
                for result in self.all_results:
                    source = result['source']
                    source_stats[source] = source_stats.get(source, 0) + 1
                
                f.write("数据源分布:\n")
                f.write("-" * 30 + "\n")
                for source, count in source_stats.items():
                    f.write(f"{source}: {count} 个数据中心\n")
                
                f.write(f"\n各省份分布:\n")
                f.write("-" * 20 + "\n")
                for province, count in province_stats.items():
                    f.write(f"{province}: {count} 个数据中心\n")
                
                # 详细列表
                province_data = {}
                for result in self.all_results:
                    province = result['province']
                    if province not in province_data:
                        province_data[province] = []
                    province_data[province].append(result)
                
                f.write(f"\n详细列表:\n")
                f.write("-" * 20 + "\n")
                
                for province, data in province_data.items():
                    f.write(f"\n{province} ({len(data)} 个):\n")
                    for i, dc in enumerate(data, 1):
                        f.write(f"  {i:2d}. {dc['name']}\n")
                        f.write(f"      坐标: ({dc['latitude']:.6f}, {dc['longitude']:.6f})\n")
                        f.write(f"      来源: {dc['source']}\n\n")
            
            print(f"✅ 最终报告已保存: {report_file}")
            
        except Exception as e:
            print(f"❌ 生成报告失败: {e}")

def main():
    """主函数"""
    print("🚀 重新爬取三省数据中心完整信息")
    print("🔍 确保获取所有遗漏的数据")
    
    # 首先对比分析
    has_missing = compare_results()
    
    if has_missing:
        print("\n⚠️ 发现遗漏数据，需要重新爬取")
    else:
        print("\n✅ 未发现遗漏，但仍进行重新爬取以确保完整性")
    
    # 重新爬取
    crawler = FinalCompleteCrawler()
    
    try:
        results = crawler.crawl_all_sources()
        
        if results:
            crawler.save_final_results()
            
            print(f"\n🎉 重新爬取任务完成！")
            print(f"✅ 成功获取 {len(results)} 个数据中心")
            print(f"✅ 确保包含所有 sichuan、si-chuan-sheng 等变体数据")
            print(f"✅ 数据已保存为重新爬取版本")
            
            print(f"\n📁 生成的文件:")
            print(f"  - 重新爬取完整三省数据中心坐标.csv")
            print(f"  - 重新爬取完整三省数据中心坐标.json")
            print(f"  - 重新爬取数据中心报告.txt")
        else:
            print("❌ 重新爬取未获取到任何数据")
            
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断任务")
    except Exception as e:
        print(f"❌ 重新爬取过程中出错: {e}")

if __name__ == "__main__":
    main()
