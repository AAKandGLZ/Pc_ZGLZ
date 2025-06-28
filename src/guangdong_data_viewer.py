#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
广东省数据中心数据查看器
用于查看和分析爬取的广东省数据中心数据
"""

import pandas as pd
import json
import os
import glob
from datetime import datetime

class GuangdongDataViewer:
    def __init__(self):
        self.data_dir = "data/guangdong"
        self.data = None
        
    def load_latest_data(self):
        """加载最新的数据文件"""
        try:
            # 查找最新的CSV文件
            csv_files = glob.glob(os.path.join(self.data_dir, "*.csv"))
            if not csv_files:
                print("❌ 未找到数据文件")
                return False
            
            # 选择最新的文件
            latest_csv = max(csv_files, key=os.path.getctime)
            print(f"📊 加载数据文件: {os.path.basename(latest_csv)}")
            
            # 读取数据
            self.data = pd.read_csv(latest_csv, encoding='utf-8-sig')
            print(f"✅ 成功加载 {len(self.data)} 条数据中心记录")
            return True
            
        except Exception as e:
            print(f"❌ 加载数据失败: {e}")
            return False
    
    def show_summary(self):
        """显示数据概览"""
        if self.data is None:
            print("❌ 请先加载数据")
            return
        
        print(f"\n{'='*60}")
        print(f"📊 广东省数据中心分布概览")
        print(f"{'='*60}")
        
        print(f"📍 总数据中心数量: {len(self.data)}")
        print(f"🗓️ 数据时间范围: {self.data['crawl_time'].min()} 到 {self.data['crawl_time'].max()}")
        
        # 城市分布
        city_counts = self.data['city'].value_counts()
        print(f"\n🏙️ 城市分布:")
        for city, count in city_counts.items():
            print(f"  {city}: {count} 个数据中心")
        
        # 坐标范围
        lat_min, lat_max = self.data['latitude'].min(), self.data['latitude'].max()
        lng_min, lng_max = self.data['longitude'].min(), self.data['longitude'].max()
        
        print(f"\n🗺️ 地理范围:")
        print(f"  纬度: {lat_min:.6f} ~ {lat_max:.6f}")
        print(f"  经度: {lng_min:.6f} ~ {lng_max:.6f}")
        print(f"  中心点: ({(lat_min+lat_max)/2:.6f}, {(lng_min+lng_max)/2:.6f})")
    
    def show_detailed_list(self, limit=10):
        """显示详细列表"""
        if self.data is None:
            print("❌ 请先加载数据")
            return
        
        print(f"\n📋 数据中心详细列表（前{limit}个）:")
        print("-" * 80)
        
        for i, row in self.data.head(limit).iterrows():
            print(f"{i+1:2d}. {row['name']}")
            print(f"    🏢 位置: {row['city']}")
            print(f"    📍 坐标: ({row['latitude']:.6f}, {row['longitude']:.6f})")
            print(f"    📊 来源: {row['source']}")
            print(f"    ⏰ 时间: {row['crawl_time']}")
            print()
        
        if len(self.data) > limit:
            print(f"... 还有 {len(self.data) - limit} 个数据中心")
    
    def search_by_city(self, city_name):
        """按城市搜索"""
        if self.data is None:
            print("❌ 请先加载数据")
            return
        
        # 模糊搜索
        results = self.data[self.data['city'].str.contains(city_name, na=False)]
        
        if len(results) == 0:
            print(f"❌ 未找到包含 '{city_name}' 的数据中心")
            return
        
        print(f"\n🔍 搜索结果: '{city_name}' ({len(results)} 个结果)")
        print("-" * 50)
        
        for i, row in results.iterrows():
            print(f"{i+1}. {row['name']}")
            print(f"   📍 ({row['latitude']:.6f}, {row['longitude']:.6f})")
            print()
    
    def search_by_name(self, name_keyword):
        """按名称关键词搜索"""
        if self.data is None:
            print("❌ 请先加载数据")
            return
        
        # 模糊搜索
        results = self.data[self.data['name'].str.contains(name_keyword, case=False, na=False)]
        
        if len(results) == 0:
            print(f"❌ 未找到包含 '{name_keyword}' 的数据中心")
            return
        
        print(f"\n🔍 搜索结果: '{name_keyword}' ({len(results)} 个结果)")
        print("-" * 50)
        
        for i, row in results.iterrows():
            print(f"{i+1}. {row['name']}")
            print(f"   🏢 {row['city']}")
            print(f"   📍 ({row['latitude']:.6f}, {row['longitude']:.6f})")
            print()
    
    def export_to_coordinates_only(self, output_file="guangdong_coordinates.txt"):
        """导出纯坐标文件"""
        if self.data is None:
            print("❌ 请先加载数据")
            return
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# 广东省数据中心坐标列表\n")
                f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 总计: {len(self.data)} 个数据中心\n")
                f.write("# 格式: 纬度,经度,名称\n\n")
                
                for _, row in self.data.iterrows():
                    f.write(f"{row['latitude']:.6f},{row['longitude']:.6f},{row['name']}\n")
            
            print(f"✅ 坐标文件已导出: {output_file}")
            
        except Exception as e:
            print(f"❌ 导出失败: {e}")
    
    def generate_statistics_report(self):
        """生成统计报告"""
        if self.data is None:
            print("❌ 请先加载数据")
            return
        
        report_file = f"reports/guangdong/数据统计分析_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("广东省数据中心统计分析报告\n")
                f.write("=" * 50 + "\n\n")
                
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"数据记录数: {len(self.data)}\n\n")
                
                # 城市分布统计
                f.write("城市分布统计:\n")
                f.write("-" * 30 + "\n")
                city_counts = self.data['city'].value_counts()
                for city, count in city_counts.items():
                    percentage = (count / len(self.data)) * 100
                    f.write(f"{city}: {count} 个 ({percentage:.1f}%)\n")
                
                # 地理分布
                f.write(f"\n地理分布:\n")
                f.write("-" * 30 + "\n")
                f.write(f"纬度范围: {self.data['latitude'].min():.6f} ~ {self.data['latitude'].max():.6f}\n")
                f.write(f"经度范围: {self.data['longitude'].min():.6f} ~ {self.data['longitude'].max():.6f}\n")
                f.write(f"中心点: ({self.data['latitude'].mean():.6f}, {self.data['longitude'].mean():.6f})\n")
                
                # 数据源统计
                f.write(f"\n数据源统计:\n")
                f.write("-" * 30 + "\n")
                source_counts = self.data['source'].value_counts()
                for source, count in source_counts.items():
                    f.write(f"{source}: {count} 个\n")
                
                # Top 10 数据中心
                f.write(f"\n主要数据中心:\n")
                f.write("-" * 30 + "\n")
                for i, row in self.data.head(10).iterrows():
                    f.write(f"{i+1:2d}. {row['name']}\n")
                    f.write(f"    位置: {row['city']}\n")
                    f.write(f"    坐标: ({row['latitude']:.6f}, {row['longitude']:.6f})\n\n")
            
            print(f"✅ 统计报告已生成: {report_file}")
            
        except Exception as e:
            print(f"❌ 生成报告失败: {e}")

def main():
    """主菜单"""
    viewer = GuangdongDataViewer()
    
    print("🔍 广东省数据中心数据查看器")
    print("=" * 50)
    
    # 自动加载数据
    if not viewer.load_latest_data():
        return
    
    while True:
        print(f"\n📋 操作菜单:")
        print("1. 显示数据概览")
        print("2. 显示详细列表")
        print("3. 按城市搜索")
        print("4. 按名称搜索")
        print("5. 导出坐标文件")
        print("6. 生成统计报告")
        print("7. 重新加载数据")
        print("0. 退出")
        
        try:
            choice = input("\n请选择操作 (0-7): ").strip()
            
            if choice == "0":
                print("👋 再见！")
                break
            elif choice == "1":
                viewer.show_summary()
            elif choice == "2":
                limit = input("显示数量 (默认10): ").strip()
                limit = int(limit) if limit.isdigit() else 10
                viewer.show_detailed_list(limit)
            elif choice == "3":
                city = input("输入城市名称: ").strip()
                if city:
                    viewer.search_by_city(city)
            elif choice == "4":
                keyword = input("输入名称关键词: ").strip()
                if keyword:
                    viewer.search_by_name(keyword)
            elif choice == "5":
                filename = input("输出文件名 (默认guangdong_coordinates.txt): ").strip()
                filename = filename if filename else "guangdong_coordinates.txt"
                viewer.export_to_coordinates_only(filename)
            elif choice == "6":
                viewer.generate_statistics_report()
            elif choice == "7":
                viewer.load_latest_data()
            else:
                print("❌ 无效选择，请重新输入")
                
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 操作出错: {e}")

if __name__ == "__main__":
    main()
