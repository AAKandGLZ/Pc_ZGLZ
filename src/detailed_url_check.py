#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细检查特定URL的所有数据
"""

import requests
import re
import json

def detailed_check_url(url, url_name):
    """详细检查单个URL的所有数据"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    print(f'\n{"="*70}')
    print(f'详细检查: {url_name}')
    print(f'URL: {url}')
    print(f'{"="*70}')
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        print(f'状态码: {response.status_code}')
        
        if response.status_code == 200:
            content = response.text
            print(f'页面大小: {len(content)} 字符')
            
            # 保存原始页面
            filename = f"{url_name.replace('/', '_').replace(':', '')}_detailed.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'页面已保存: {filename}')
            
            # 提取所有坐标
            latitudes = re.findall(r'"latitude":\s*([\d\.\-]+)', content)
            longitudes = re.findall(r'"longitude":\s*([\d\.\-]+)', content)
            
            print(f'\n坐标统计: {len(latitudes)} 个纬度, {len(longitudes)} 个经度')
            
            if latitudes and len(latitudes) == len(longitudes):
                print(f'\n所有发现的坐标:')
                coordinates = []
                for i, (lat, lng) in enumerate(zip(latitudes, longitudes)):
                    coord_data = {
                        'index': i + 1,
                        'latitude': float(lat),
                        'longitude': float(lng),
                        'coordinates': f"{lat},{lng}"
                    }
                    coordinates.append(coord_data)
                    print(f'  {i+1:2d}. ({lat}, {lng})')
                
                # 提取所有可能的名称
                name_patterns = [
                    r'"name":\s*"([^"]+)"',
                    r'"title":\s*"([^"]+)"',
                    r'"displayName":\s*"([^"]+)"',
                    r'"label":\s*"([^"]+)"',
                ]
                
                all_names = []
                for pattern in name_patterns:
                    names = re.findall(pattern, content, re.IGNORECASE)
                    all_names.extend(names)
                
                # 过滤和去重名称
                filtered_names = []
                seen_names = set()
                for name in all_names:
                    clean_name = name.strip()
                    if (len(clean_name) > 3 and 
                        len(clean_name) < 150 and 
                        clean_name not in seen_names and
                        any(keyword in clean_name.lower() for keyword in 
                            ['data center', 'idc', '数据中心', 'center', 'chengdu', 'sichuan', 'telecom', 'gds', 'ctu'])):
                        filtered_names.append(clean_name)
                        seen_names.add(clean_name)
                
                print(f'\n找到的数据中心名称 ({len(filtered_names)} 个):')
                for i, name in enumerate(filtered_names[:20], 1):  # 显示前20个
                    print(f'  {i:2d}. {name}')
                
                # 检查是否还有其他坐标格式
                other_patterns = [
                    r'"lat":\s*([\d\.\-]+)',
                    r'"lng":\s*([\d\.\-]+)',
                    r'position.*?(\d{2}\.\d+),\s*(\d{3}\.\d+)',
                    r'marker.*?(\d{2}\.\d+),\s*(\d{3}\.\d+)',
                ]
                
                print(f'\n检查其他坐标格式:')
                for pattern in other_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        print(f'  模式 "{pattern}": {len(matches)} 个匹配')
                
                # 保存结果
                result_data = {
                    'url': url,
                    'url_name': url_name,
                    'total_coordinates': len(coordinates),
                    'coordinates': coordinates,
                    'names': filtered_names[:len(coordinates)]  # 名称数量与坐标匹配
                }
                
                result_filename = f"{url_name.replace('/', '_').replace(':', '')}_result.json"
                with open(result_filename, 'w', encoding='utf-8') as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=2)
                print(f'\n结果已保存: {result_filename}')
                
                return coordinates, filtered_names
            
            else:
                print('坐标数据不完整或未找到')
                return [], []
                
        else:
            print(f'请求失败: {response.status_code}')
            return [], []
            
    except Exception as e:
        print(f'检查失败: {e}')
        return [], []

def main():
    """主函数"""
    print('详细检查指定URL的所有数据')
    
    # 要检查的URL
    urls_to_check = [
        ('https://www.datacenters.com/locations/china/si-chuan-sheng', 'si-chuan-sheng'),
        ('https://www.datacenters.com/locations/china/sichuan', 'sichuan'),
    ]
    
    all_results = {}
    
    for url, name in urls_to_check:
        coordinates, names = detailed_check_url(url, name)
        all_results[name] = {
            'coordinates': coordinates,
            'names': names,
            'count': len(coordinates)
        }
    
    # 汇总结果
    print(f'\n{"="*70}')
    print('汇总结果:')
    print(f'{"="*70}')
    
    total_coords = 0
    for name, data in all_results.items():
        count = data['count']
        total_coords += count
        print(f'{name}: {count} 个数据中心')
    
    print(f'总计: {total_coords} 个数据中心')
    
    # 检查是否有重复坐标
    all_coords = set()
    unique_coords = []
    
    for name, data in all_results.items():
        for coord in data['coordinates']:
            coord_key = (round(coord['latitude'], 6), round(coord['longitude'], 6))
            if coord_key not in all_coords:
                all_coords.add(coord_key)
                unique_coords.append(coord)
    
    print(f'去重后: {len(unique_coords)} 个唯一坐标')
    
    # 保存最终汇总
    final_result = {
        'summary': {
            'total_coordinates': len(unique_coords),
            'sources': list(all_results.keys()),
            'check_time': '2025-06-20'
        },
        'unique_coordinates': unique_coords,
        'source_details': all_results
    }
    
    with open('详细检查结果汇总.json', 'w', encoding='utf-8') as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)
    
    print('\n详细检查完成！')
    print('生成的文件:')
    for name in all_results.keys():
        print(f'  - {name.replace("/", "_").replace(":", "")}_detailed.html')
        print(f'  - {name.replace("/", "_").replace(":", "")}_result.json')
    print('  - 详细检查结果汇总.json')

if __name__ == "__main__":
    main()
