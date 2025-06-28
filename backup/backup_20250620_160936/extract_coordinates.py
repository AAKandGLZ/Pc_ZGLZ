#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从HTML源码中提取坐标数据
"""

import re
import json

def extract_coordinates_from_html():
    """从HTML文件中提取坐标"""
    try:
        with open("e:\\空间统计分析\\爬虫\\page_source.html", "r", encoding="utf-8") as f:
            content = f.read()
        
        print("从HTML源码中提取坐标数据...")
        
        # 提取纬度和经度
        latitudes = re.findall(r'"latitude":\s*([\d\.\-]+)', content)
        longitudes = re.findall(r'"longitude":\s*([\d\.\-]+)', content)
        
        print(f"找到 {len(latitudes)} 个纬度值")
        print(f"找到 {len(longitudes)} 个经度值")
        
        if len(latitudes) == len(longitudes):
            coordinates = []
            for i, (lat, lng) in enumerate(zip(latitudes, longitudes)):
                coord_data = {
                    "index": i + 1,
                    "latitude": float(lat),
                    "longitude": float(lng),
                    "province": "四川省",
                    "name": f"四川省数据中心{i+1}",
                    "source": "HTML解析"
                }
                coordinates.append(coord_data)
                print(f"{i+1}. 坐标: ({lat}, {lng})")
            
            # 保存提取的坐标
            with open("e:\\空间统计分析\\爬虫\\extracted_coordinates.json", "w", encoding="utf-8") as f:
                json.dump(coordinates, f, ensure_ascii=False, indent=2)
            
            print(f"\n成功提取 {len(coordinates)} 个坐标")
            print("坐标已保存到 extracted_coordinates.json")
            
            return coordinates
        else:
            print("纬度和经度数量不匹配")
            return []
            
    except Exception as e:
        print(f"提取坐标失败: {e}")
        return []

def search_for_addresses():
    """搜索地址信息"""
    try:
        with open("e:\\空间统计分析\\爬虫\\page_source.html", "r", encoding="utf-8") as f:
            content = f.read()
        
        print("\n搜索地址信息...")
        
        # 搜索可能的地址模式
        address_patterns = [
            r'"address":\s*"([^"]+)"',
            r'"location":\s*"([^"]+)"',
            r'"city":\s*"([^"]+)"',
            r'"name":\s*"([^"]+)"',
            r'China[^"]*Sichuan[^"]*',
            r'四川[^"]*',
            r'成都[^"]*'
        ]
        
        found_addresses = []
        
        for pattern in address_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                print(f"模式 '{pattern}' 找到 {len(matches)} 个匹配:")
                for match in matches[:5]:  # 只显示前5个
                    print(f"  - {match}")
                found_addresses.extend(matches)
        
        return found_addresses
        
    except Exception as e:
        print(f"搜索地址失败: {e}")
        return []

def main():
    """主函数"""
    print("=" * 60)
    print("坐标数据提取器")
    print("=" * 60)
    
    coordinates = extract_coordinates_from_html()
    addresses = search_for_addresses()
    
    if coordinates:
        print(f"\n成功提取了四川省的 {len(coordinates)} 个数据中心坐标")
        print("这些坐标数据可以用于进一步的空间统计分析")
    else:
        print("\n未能提取到坐标数据")

if __name__ == "__main__":
    main()
