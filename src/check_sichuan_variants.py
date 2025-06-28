#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查新发现的四川省URL变体
"""

import requests
import re
import json

def check_si_chuan_sheng():
    """检查 si-chuan-sheng URL"""
    
    url = 'https://www.datacenters.com/locations/china/si-chuan-sheng'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    print(f'检查新发现的四川省URL: {url}')
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f'状态码: {response.status_code}')
        
        if response.status_code == 200:
            content = response.text
            print(f'页面大小: {len(content)} 字符')
            
            # 检查坐标数据
            lat_matches = re.findall(r'"latitude":\s*([\d\.\-]+)', content)
            lng_matches = re.findall(r'"longitude":\s*([\d\.\-]+)', content)
            
            print(f'坐标数据: {len(lat_matches)} 个纬度, {len(lng_matches)} 个经度')
            
            if lat_matches and len(lat_matches) == len(lng_matches):
                print(f'\n发现 {len(lat_matches)} 个数据中心坐标:')
                
                # 提取名称
                name_patterns = [
                    r'"name":\s*"([^"]*(?:Data Center|IDC|数据中心)[^"]*)"',
                    r'"title":\s*"([^"]*(?:Data Center|IDC|数据中心)[^"]*)"',
                ]
                
                all_names = []
                for pattern in name_patterns:
                    names = re.findall(pattern, content, re.IGNORECASE)
                    all_names.extend(names)
                
                unique_names = list(set([name.strip() for name in all_names if name.strip()]))
                
                # 显示坐标和名称
                for i, (lat, lng) in enumerate(zip(lat_matches, lng_matches)):
                    name = unique_names[i] if i < len(unique_names) else f"四川省数据中心{i+1}"
                    print(f'  {i+1:2d}. {name}')
                    print(f'      坐标: ({lat}, {lng})')
                
                # 保存页面
                with open('si_chuan_sheng_page.html', 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f'\n页面已保存到: si_chuan_sheng_page.html')
                
                return lat_matches, lng_matches, unique_names
            
            elif lat_matches:
                print('坐标数据不完整（纬度和经度数量不匹配）')
            else:
                print('未找到坐标数据')
                
        elif response.status_code == 404:
            print('URL不存在（404错误）')
        else:
            print(f'请求失败，状态码: {response.status_code}')
            
    except Exception as e:
        print(f'检查失败: {e}')
    
    return [], [], []

def check_all_sichuan_variants():
    """检查所有可能的四川省URL变体"""
    
    sichuan_urls = [
        'https://www.datacenters.com/locations/china/sichuan-sheng',
        'https://www.datacenters.com/locations/china/si-chuan-sheng',
        'https://www.datacenters.com/locations/china/sichuan',
        'https://www.datacenters.com/locations/china/si-chuan',
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    all_found_data = []
    
    print('检查所有四川省URL变体:')
    print('=' * 60)
    
    for url in sichuan_urls:
        print(f'\n检查: {url}')
        try:
            response = requests.get(url, headers=headers, timeout=15)
            print(f'状态: {response.status_code}')
            
            if response.status_code == 200:
                content = response.text
                lat_matches = re.findall(r'"latitude":\s*([\d\.\-]+)', content)
                lng_matches = re.findall(r'"longitude":\s*([\d\.\-]+)', content)
                
                print(f'坐标: {len(lat_matches)} 个纬度, {len(lng_matches)} 个经度')
                
                if lat_matches and len(lat_matches) == len(lng_matches):
                    url_key = url.split('/')[-1]
                    
                    for i, (lat, lng) in enumerate(zip(lat_matches, lng_matches)):
                        data = {
                            'url_source': url_key,
                            'latitude': float(lat),
                            'longitude': float(lng),
                            'index': i + 1
                        }
                        all_found_data.append(data)
                
            elif response.status_code == 404:
                print('URL不存在')
            else:
                print(f'其他错误: {response.status_code}')
                
        except Exception as e:
            print(f'请求失败: {e}')
    
    print(f'\n总结:')
    print(f'总共找到 {len(all_found_data)} 个坐标')
    
    # 按URL分组统计
    url_stats = {}
    for data in all_found_data:
        url = data['url_source']
        url_stats[url] = url_stats.get(url, 0) + 1
    
    for url, count in url_stats.items():
        print(f'{url}: {count} 个坐标')
    
    return all_found_data

def main():
    print('检查四川省新URL变体')
    print('=' * 40)
    
    # 首先检查 si-chuan-sheng
    lat_matches, lng_matches, names = check_si_chuan_sheng()
    
    print('\n' + '=' * 60)
    
    # 然后检查所有变体
    all_data = check_all_sichuan_variants()
    
    # 保存结果
    if all_data:
        with open('四川省所有URL数据.json', 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        print(f'\n所有数据已保存到: 四川省所有URL数据.json')

if __name__ == "__main__":
    main()
