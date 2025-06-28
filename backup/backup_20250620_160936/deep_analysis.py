#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度分析网站数据，查找遗漏的数据中心信息
"""

import requests
import re
import json

def deep_analysis():
    """深度分析所有省份的数据"""
    
    provinces = {
        "四川省": "https://www.datacenters.com/locations/china/sichuan-sheng",
        "云南省": "https://www.datacenters.com/locations/china/yunnan-sheng", 
        "贵州省": "https://www.datacenters.com/locations/china/guizhou-sheng"
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    all_found_data = []
    
    for province, url in provinces.items():
        print(f"\n{'='*60}")
        print(f"深度分析: {province}")
        print(f"URL: {url}")
        print(f"{'='*60}")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            print(f"状态码: {response.status_code}")
            print(f"页面大小: {len(response.text)} 字符")
            
            if response.status_code != 200:
                continue
            
            content = response.text
            
            # 保存原始页面用于分析
            with open(f"{province}_full_page.html", "w", encoding="utf-8") as f:
                f.write(content)
            
            # 多种坐标提取模式
            coordinate_patterns = [
                # JSON格式坐标
                (r'"latitude":\s*([\d\.\-]+)', r'"longitude":\s*([\d\.\-]+)'),
                (r'"lat":\s*([\d\.\-]+)', r'"lng":\s*([\d\.\-]+)'),
                # 直接坐标对
                (r'(\d{2}\.\d{4,}),\s*(\d{3}\.\d{4,})', None),
                # 其他可能格式
                (r'position.*?(\d{2}\.\d+),\s*(\d{3}\.\d+)', None),
            ]
            
            found_coordinates = []
            
            for lat_pattern, lng_pattern in coordinate_patterns:
                if lng_pattern:
                    # 分别提取纬度和经度
                    lats = re.findall(lat_pattern, content)
                    lngs = re.findall(lng_pattern, content)
                    
                    if lats and lngs:
                        print(f"模式匹配: 找到 {len(lats)} 个纬度, {len(lngs)} 个经度")
                        
                        # 配对坐标
                        for lat, lng in zip(lats, lngs):
                            try:
                                lat_f = float(lat)
                                lng_f = float(lng)
                                # 验证坐标范围是否合理
                                if 15 <= lat_f <= 35 and 95 <= lng_f <= 115:
                                    found_coordinates.append((lat_f, lng_f))
                            except:
                                continue
                else:
                    # 直接提取坐标对
                    coords = re.findall(lat_pattern, content)
                    if coords:
                        print(f"坐标对模式: 找到 {len(coords)} 个坐标对")
                        for coord in coords:
                            if isinstance(coord, tuple) and len(coord) == 2:
                                try:
                                    lat_f = float(coord[0])
                                    lng_f = float(coord[1])
                                    if 15 <= lat_f <= 35 and 95 <= lng_f <= 115:
                                        found_coordinates.append((lat_f, lng_f))
                                except:
                                    continue
            
            # 去重
            unique_coords = list(set(found_coordinates))
            print(f"去重后坐标数: {len(unique_coords)}")
            
            # 提取名称信息
            name_patterns = [
                r'"name":\s*"([^"]*(?:Data Center|IDC|数据中心|Center)[^"]*)"',
                r'"title":\s*"([^"]*(?:Data Center|IDC|数据中心|Center)[^"]*)"',
                r'"name":\s*"([^"]*(?:' + province.replace('省', '') + '|Sichuan|Yunnan|Guizhou)[^"]*)"',
                r'(?:>|\s)([^<>]*(?:Data Center|IDC|数据中心)[^<>]*)(?:<|$)',
            ]
            
            all_names = []
            for pattern in name_patterns:
                names = re.findall(pattern, content, re.IGNORECASE)
                all_names.extend(names)
            
            # 去重名称
            unique_names = list(set([name.strip() for name in all_names if name.strip()]))
            print(f"找到 {len(unique_names)} 个唯一名称")
            
            # 组合数据
            province_data = []
            for i, (lat, lng) in enumerate(unique_coords):
                name = unique_names[i] if i < len(unique_names) else f"{province}数据中心{i+1}"
                
                data = {
                    'province': province,
                    'latitude': lat,
                    'longitude': lng,
                    'name': name,
                    'index': i + 1
                }
                
                province_data.append(data)
                print(f"  {i+1}. {name} - ({lat:.6f}, {lng:.6f})")
            
            all_found_data.extend(province_data)
            
            # 检查特殊关键词
            special_keywords = ['Sichuan', 'Si Chuan Sheng', 'Guizhou', 'Yunnan']
            for keyword in special_keywords:
                count = len(re.findall(keyword, content, re.IGNORECASE))
                if count > 0:
                    print(f"关键词 '{keyword}' 出现 {count} 次")
            
        except Exception as e:
            print(f"分析 {province} 失败: {e}")
    
    # 保存完整结果
    print(f"\n{'='*60}")
    print(f"总结果: 找到 {len(all_found_data)} 个数据中心")
    
    with open("完整数据中心数据.json", "w", encoding="utf-8") as f:
        json.dump(all_found_data, f, ensure_ascii=False, indent=2)
    
    # 按省份统计
    province_count = {}
    for data in all_found_data:
        province = data['province']
        province_count[province] = province_count.get(province, 0) + 1
    
    for province, count in province_count.items():
        print(f"{province}: {count} 个")
    
    return all_found_data

if __name__ == "__main__":
    deep_analysis()
