#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查看爬取结果的脚本
"""

import json
import pandas as pd
import os

def check_results():
    """检查爬取结果文件"""
    base_path = "e:\\空间统计分析\\爬虫"
    
    result_files = [
        "datacenter_final_results.csv",
        "datacenter_final_results.json",
        "datacenter_results.csv", 
        "datacenter_results.json",
        "data_centers.csv",
        "data_centers.json"
    ]
    
    print("=" * 60)
    print("数据中心爬取结果查看器")
    print("=" * 60)
    
    found_files = []
    
    for filename in result_files:
        filepath = os.path.join(base_path, filename)
        if os.path.exists(filepath):
            found_files.append(filepath)
            size = os.path.getsize(filepath)
            print(f"找到文件: {filename} ({size} 字节)")
    
    if not found_files:
        print("未找到任何结果文件")
        print("请先运行爬虫程序")
        return
    
    # 读取最新的结果文件
    latest_file = None
    latest_time = 0
    
    for filepath in found_files:
        if filepath.endswith('.json'):
            mtime = os.path.getmtime(filepath)
            if mtime > latest_time:
                latest_time = mtime
                latest_file = filepath
    
    if latest_file:
        print(f"\n读取最新结果文件: {os.path.basename(latest_file)}")
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if data:
                print(f"\n总数据中心数量: {len(data)}")
                
                # 按省份统计
                province_count = {}
                for item in data:
                    province = item.get('province', '未知')
                    province_count[province] = province_count.get(province, 0) + 1
                
                print("\n各省份分布:")
                for province, count in province_count.items():
                    print(f"  {province}: {count} 个")
                
                print(f"\n详细数据:")
                print("-" * 60)
                
                for i, item in enumerate(data, 1):
                    print(f"{i:2d}. {item.get('province', '未知')} - {item.get('name', '未知')}")
                    print(f"    坐标: ({item.get('latitude', 0):.6f}, {item.get('longitude', 0):.6f})")
                    if item.get('address'):
                        print(f"    地址: {item['address']}")
                    print("-" * 40)
            else:
                print("结果文件为空")
                
        except Exception as e:
            print(f"读取结果文件失败: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    check_results()
