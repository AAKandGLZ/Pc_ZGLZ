#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查找所有可能的数据中心信息源
"""

import requests
import re
import json

def search_all_sources():
    """搜索所有可能的数据源"""
    
    # 尝试不同的URL格式
    test_urls = [
        'https://www.datacenters.com/locations/china/sichuan-sheng',
        'https://www.datacenters.com/locations/china/yunnan-sheng',
        'https://www.datacenters.com/locations/china/guizhou-sheng',
        'https://www.datacenters.com/locations/china/sichuan',
        'https://www.datacenters.com/locations/china/yunnan',
        'https://www.datacenters.com/locations/china/guizhou',
        'https://www.datacenters.com/locations/china',  # 总页面
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for url in test_urls:
        print(f"\n检测: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=15)
            print(f"状态: {response.status_code}")
            
            if response.status_code == 200:
                content = response.text
                
                # 检查坐标数据
                lat_matches = re.findall(r'"latitude":\s*([\d\.\-]+)', content)
                lng_matches = re.findall(r'"longitude":\s*([\d\.\-]+)', content)
                
                print(f"坐标数据: {len(lat_matches)} 个纬度, {len(lng_matches)} 个经度")
                
                # 检查关键词
                sichuan_count = len(re.findall(r'sichuan|四川', content, re.IGNORECASE))
                yunnan_count = len(re.findall(r'yunnan|云南', content, re.IGNORECASE))
                guizhou_count = len(re.findall(r'guizhou|贵州', content, re.IGNORECASE))
                
                print(f"关键词统计: Sichuan({sichuan_count}), Yunnan({yunnan_count}), Guizhou({guizhou_count})")
                
                # 如果有数据，保存页面
                if lat_matches:
                    filename = url.split('/')[-1] + '_page.html'
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"页面已保存: {filename}")
                    
        except Exception as e:
            print(f"错误: {e}")

def extract_comprehensive_data():
    """综合提取所有数据"""
    
    # 从四川省页面提取更全面的数据
    sichuan_url = 'https://www.datacenters.com/locations/china/sichuan-sheng'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    print("=== 综合数据提取 ===")
    
    try:
        response = requests.get(sichuan_url, headers=headers)
        content = response.text
        
        # 使用多种方式提取坐标
        coordinate_methods = [
            # 方法1: JSON格式
            (r'"latitude":\s*([\d\.\-]+)', r'"longitude":\s*([\d\.\-]+)'),
            # 方法2: 可能的其他格式
            (r'"lat":\s*([\d\.\-]+)', r'"lng":\s*([\d\.\-]+)'),
            # 方法3: 直接坐标对
            (r'(\d{2}\.\d+),\s*(\d{3}\.\d+)', None)
        ]
        
        all_coordinates = set()
        
        for i, (lat_pattern, lng_pattern) in enumerate(coordinate_methods, 1):
            print(f"\n方法 {i}:")
            
            if lng_pattern:
                lats = re.findall(lat_pattern, content)
                lngs = re.findall(lng_pattern, content)
                print(f"  找到 {len(lats)} 个纬度, {len(lngs)} 个经度")
                
                for lat, lng in zip(lats, lngs):
                    try:
                        lat_f, lng_f = float(lat), float(lng)
                        if 20 <= lat_f <= 35 and 100 <= lng_f <= 110:  # 中国西南地区范围
                            all_coordinates.add((lat_f, lng_f))
                    except:
                        pass
            else:
                coords = re.findall(lat_pattern, content)
                print(f"  找到 {len(coords)} 个坐标对")
                for coord in coords:
                    if isinstance(coord, tuple) and len(coord) == 2:
                        try:
                            lat_f, lng_f = float(coord[0]), float(coord[1])
                            if 20 <= lat_f <= 35 and 100 <= lng_f <= 110:
                                all_coordinates.add((lat_f, lng_f))
                        except:
                            pass
        
        print(f"\n去重后总坐标数: {len(all_coordinates)}")
        
        # 提取所有可能的数据中心名称
        name_patterns = [
            r'"name":\s*"([^"]*(?:Data Center|IDC|数据中心)[^"]*)"',
            r'"title":\s*"([^"]*(?:Data Center|IDC|数据中心)[^"]*)"',
            r'>([^<>]*(?:Data Center|IDC|数据中心)[^<>]*)<',
            r'([A-Za-z\s]+(?:Data Center|IDC))',
            r'((?:Chengdu|Mianyang|Neijiang|Yibin|Ziyang|Dazhou|Panzhihua|Nanchong|GDS|QTS|CTU)[^,\.\n]*(?:Data Center|IDC|Center)?)',
        ]
        
        all_names = set()
        for pattern in name_patterns:
            names = re.findall(pattern, content, re.IGNORECASE)
            for name in names:
                clean_name = name.strip()
                if len(clean_name) > 3 and len(clean_name) < 100:  # 过滤太短或太长的名称
                    all_names.add(clean_name)
        
        print(f"找到 {len(all_names)} 个唯一名称")
        
        # 显示所有找到的坐标
        sorted_coords = sorted(list(all_coordinates))
        for i, (lat, lng) in enumerate(sorted_coords, 1):
            print(f"{i:2d}. ({lat:.6f}, {lng:.6f})")
        
        # 显示部分名称
        print(f"\n数据中心名称示例:")
        for i, name in enumerate(sorted(list(all_names))[:20], 1):
            print(f"{i:2d}. {name}")
        
        return sorted_coords, sorted(list(all_names))
        
    except Exception as e:
        print(f"提取失败: {e}")
        return [], []

def main():
    print("开始搜索所有可能的数据源...")
    search_all_sources()
    
    print("\n" + "="*60)
    print("开始综合数据提取...")
    coordinates, names = extract_comprehensive_data()
    
    print(f"\n最终结果:")
    print(f"总坐标数: {len(coordinates)}")
    print(f"总名称数: {len(names)}")

if __name__ == "__main__":
    main()
