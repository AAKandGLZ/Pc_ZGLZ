#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目整理脚本 - 整理代码文件夹结构
"""

import os
import shutil
import json
from datetime import datetime

class ProjectOrganizer:
    def __init__(self):
        self.root_dir = os.getcwd()
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 定义文件分类规则
        self.file_categories = {
            'python_scripts': {
                'extensions': ['.py'],
                'target_dir': 'src',
                'description': 'Python脚本文件'
            },
            'data_files': {
                'extensions': ['.json', '.csv'],
                'target_dir': 'data',
                'description': '数据文件'
            },
            'html_files': {
                'extensions': ['.html'],
                'target_dir': 'html_sources',
                'description': 'HTML源码文件'
            },
            'reports': {
                'extensions': ['.txt', '.md'],
                'patterns': ['报告', '统计', '分析', '检查', 'README', 'DEPLOYMENT'],
                'target_dir': 'reports',
                'description': '报告和文档文件'
            },
            'config_files': {
                'extensions': ['.bat', '.txt'],
                'patterns': ['requirements', 'install', 'run_', 'git_', 'commands'],
                'target_dir': 'scripts',
                'description': '配置和运行脚本'
            },
            'docs': {
                'extensions': ['.md'],
                'patterns': ['README', 'LICENSE', 'CHECKLIST', 'PUBLISH'],
                'target_dir': 'docs',
                'description': '项目文档'
            }
        }
        
        # 需要创建的目录结构
        self.directories = [
            'src',           # 源代码
            'data',          # 数据文件
            'data/guangdong', # 广东省数据
            'data/archive',   # 旧数据归档
            'html_sources',   # HTML源码
            'html_sources/guangdong', # 广东省HTML
            'html_sources/archive',   # 旧HTML归档
            'reports',        # 报告
            'reports/guangdong', # 广东省报告
            'reports/archive',   # 旧报告归档
            'scripts',        # 脚本文件
            'docs',           # 文档
            'backup'          # 备份
        ]
    
    def create_directory_structure(self):
        """创建目录结构"""
        print("📁 创建目录结构...")
        
        for directory in self.directories:
            dir_path = os.path.join(self.root_dir, directory)
            os.makedirs(dir_path, exist_ok=True)
            print(f"  ✅ 创建目录: {directory}")
        
        print("✅ 目录结构创建完成")
    
    def analyze_files(self):
        """分析当前目录中的文件"""
        print("\n🔍 分析当前文件...")
        
        files_info = []
        
        for filename in os.listdir(self.root_dir):
            if os.path.isfile(os.path.join(self.root_dir, filename)):
                file_info = {
                    'name': filename,
                    'extension': os.path.splitext(filename)[1].lower(),
                    'size': os.path.getsize(filename),
                    'category': self.categorize_file(filename),
                    'target_dir': None
                }
                
                # 确定目标目录
                category = file_info['category']
                if category in self.file_categories:
                    file_info['target_dir'] = self.file_categories[category]['target_dir']
                
                files_info.append(file_info)
                print(f"  📄 {filename} -> {file_info['category']} -> {file_info['target_dir']}")
        
        return files_info
    
    def categorize_file(self, filename):
        """根据文件名和扩展名分类文件"""
        filename_lower = filename.lower()
        file_ext = os.path.splitext(filename)[1].lower()
        
        for category, rules in self.file_categories.items():
            # 检查扩展名
            if 'extensions' in rules and file_ext in rules['extensions']:
                # 如果有patterns，需要额外检查
                if 'patterns' in rules:
                    for pattern in rules['patterns']:
                        if pattern.lower() in filename_lower:
                            return category
                    # 如果没有匹配的pattern，继续检查其他类别
                    continue
                else:
                    return category
            
            # 检查文件名模式（对于没有扩展名检查的情况）
            if 'patterns' in rules and 'extensions' not in rules:
                for pattern in rules['patterns']:
                    if pattern.lower() in filename_lower:
                        return category
        
        return 'other'
    
    def backup_files(self, files_info):
        """备份原始文件"""
        print(f"\n💾 备份原始文件...")
        
        backup_dir = os.path.join(self.root_dir, 'backup', f'backup_{self.timestamp}')
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_count = 0
        for file_info in files_info:
            source_path = os.path.join(self.root_dir, file_info['name'])
            backup_path = os.path.join(backup_dir, file_info['name'])
            
            try:
                shutil.copy2(source_path, backup_path)
                backup_count += 1
                print(f"  ✅ 备份: {file_info['name']}")
            except Exception as e:
                print(f"  ❌ 备份失败 {file_info['name']}: {e}")
        
        print(f"✅ 备份完成，共备份 {backup_count} 个文件")
        return backup_dir
    
    def organize_files(self, files_info):
        """整理文件到对应目录"""
        print(f"\n📂 整理文件...")
        
        organized_count = 0
        
        for file_info in files_info:
            if file_info['target_dir'] is None:
                print(f"  ⚠️  跳过未分类文件: {file_info['name']}")
                continue
            
            source_path = os.path.join(self.root_dir, file_info['name'])
            target_dir = os.path.join(self.root_dir, file_info['target_dir'])
            target_path = os.path.join(target_dir, file_info['name'])
            
            # 检查目标文件是否已存在
            if os.path.exists(target_path):
                # 如果存在，重命名
                base_name, ext = os.path.splitext(file_info['name'])
                counter = 1
                while os.path.exists(target_path):
                    new_name = f"{base_name}_{counter}{ext}"
                    target_path = os.path.join(target_dir, new_name)
                    counter += 1
                print(f"  📄 文件已存在，重命名为: {os.path.basename(target_path)}")
            
            try:
                shutil.move(source_path, target_path)
                organized_count += 1
                print(f"  ✅ 移动: {file_info['name']} -> {file_info['target_dir']}/")
            except Exception as e:
                print(f"  ❌ 移动失败 {file_info['name']}: {e}")
        
        print(f"✅ 文件整理完成，共整理 {organized_count} 个文件")
    
    def handle_special_files(self):
        """处理特殊文件"""
        print(f"\n🔧 处理特殊文件...")
        
        special_moves = [
            # 将旧的省份数据移到归档目录
            ('四川省*.html', 'html_sources/archive/'),
            ('云南省*.html', 'html_sources/archive/'),
            ('贵州省*.html', 'html_sources/archive/'),
            ('*三省数据中心坐标*', 'data/archive/'),
            ('*三省*.txt', 'reports/archive/'),
        ]
        
        import glob
        
        for pattern, target_dir in special_moves:
            target_path = os.path.join(self.root_dir, target_dir)
            os.makedirs(target_path, exist_ok=True)
            
            matching_files = glob.glob(pattern)
            for file_path in matching_files:
                if os.path.isfile(file_path):
                    filename = os.path.basename(file_path)
                    dest_path = os.path.join(target_path, filename)
                    
                    try:
                        shutil.move(file_path, dest_path)
                        print(f"  ✅ 归档: {filename} -> {target_dir}")
                    except Exception as e:
                        print(f"  ❌ 归档失败 {filename}: {e}")
    
    def generate_project_structure_report(self):
        """生成项目结构报告"""
        print(f"\n📊 生成项目结构报告...")
        
        report_path = os.path.join(self.root_dir, 'reports', f'项目结构报告_{self.timestamp}.txt')
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("项目结构整理报告\n")
                f.write("=" * 50 + "\n\n")
                
                f.write(f"整理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"项目根目录: {self.root_dir}\n\n")
                
                f.write("目录结构:\n")
                f.write("-" * 30 + "\n")
                
                for directory in self.directories:
                    dir_path = os.path.join(self.root_dir, directory)
                    if os.path.exists(dir_path):
                        file_count = len([f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))])
                        f.write(f"{directory}/  ({file_count} 个文件)\n")
                        
                        # 列出目录中的文件
                        for filename in os.listdir(dir_path):
                            file_path = os.path.join(dir_path, filename)
                            if os.path.isfile(file_path):
                                f.write(f"  - {filename}\n")
                        f.write("\n")
                
                f.write("文件分类规则:\n")
                f.write("-" * 30 + "\n")
                for category, rules in self.file_categories.items():
                    f.write(f"{category}: {rules['description']}\n")
                    f.write(f"  目标目录: {rules['target_dir']}\n")
                    if 'extensions' in rules:
                        f.write(f"  扩展名: {', '.join(rules['extensions'])}\n")
                    if 'patterns' in rules:
                        f.write(f"  文件名模式: {', '.join(rules['patterns'])}\n")
                    f.write("\n")
            
            print(f"✅ 项目结构报告已保存: {report_path}")
            
        except Exception as e:
            print(f"❌ 生成报告失败: {e}")
    
    def create_readme(self):
        """创建项目README文件"""
        readme_path = os.path.join(self.root_dir, 'docs', 'README.md')
        
        readme_content = f"""# 数据中心爬虫项目

## 项目概述
本项目专门用于爬取中国各省市的数据中心分布信息，当前主要支持广东省数据中心信息的采集和分析。

## 项目结构
```
Pc_ZGLZ/
├── src/                    # 源代码
│   └── guangdong_datacenter_crawler.py
├── data/                   # 数据文件
│   ├── guangdong/         # 广东省数据
│   └── archive/           # 归档数据
├── html_sources/          # HTML源码
│   ├── guangdong/         # 广东省HTML
│   └── archive/           # 旧HTML归档
├── reports/               # 报告文件
│   ├── guangdong/         # 广东省报告
│   └── archive/           # 旧报告归档
├── scripts/               # 脚本文件
├── docs/                  # 项目文档
└── backup/                # 备份文件
```

## 使用方法

### 广东省数据中心爬虫
```bash
python src/guangdong_datacenter_crawler.py
```

该脚本会：
1. 爬取广东省及主要城市的数据中心信息
2. 包含深圳、广州、东莞、佛山、珠海、中山、惠州等城市
3. 自动去重和数据验证
4. 生成CSV、JSON格式的数据文件
5. 生成详细的分析报告

### 项目整理
```bash
python scripts/organize_project.py
```

## 输出文件说明

### 数据文件
- `data/guangdong/广东省数据中心坐标_[时间戳].csv` - CSV格式数据
- `data/guangdong/广东省数据中心坐标_[时间戳].json` - JSON格式数据

### 报告文件
- `reports/guangdong/广东省数据中心分布报告_[时间戳].txt` - 详细分析报告

### 调试文件
- `html_sources/guangdong/` - 保存的HTML源码（用于调试）

## 技术特点

1. **多URL策略**: 使用多种URL变体提高数据覆盖率
2. **智能去重**: 基于坐标精度去除重复数据
3. **地理验证**: 仅保留广东省地理范围内的坐标
4. **容错处理**: 完善的异常处理和错误恢复
5. **详细日志**: 完整的爬取过程记录

## 依赖包
- requests - HTTP请求
- pandas - 数据处理
- json - JSON数据处理
- re - 正则表达式

## 安装依赖
```bash
pip install -r requirements.txt
```

## 更新日志

### {datetime.now().strftime('%Y-%m-%d')}
- 创建广东省专用数据中心爬虫
- 重构项目目录结构
- 添加自动化项目整理功能
- 完善文档和使用说明

## 许可证
本项目仅供学习和研究使用。

## 联系方式
如有问题请提交Issue或联系项目维护者。
"""
        
        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            print(f"✅ README文件已创建: {readme_path}")
        except Exception as e:
            print(f"❌ 创建README失败: {e}")
    
    def run_full_organization(self):
        """运行完整的项目整理流程"""
        print("🚀 启动项目整理...")
        print("="*60)
        
        try:
            # 1. 创建目录结构
            self.create_directory_structure()
            
            # 2. 分析文件
            files_info = self.analyze_files()
            
            # 3. 备份文件
            backup_dir = self.backup_files(files_info)
            
            # 4. 整理文件
            self.organize_files(files_info)
            
            # 5. 处理特殊文件
            self.handle_special_files()
            
            # 6. 生成报告
            self.generate_project_structure_report()
            
            # 7. 创建README
            self.create_readme()
            
            print("\n" + "="*60)
            print("🎉 项目整理完成！")
            print(f"✅ 文件已按类别整理")
            print(f"✅ 备份已保存到: backup/backup_{self.timestamp}/")
            print(f"✅ 项目结构报告已生成")
            print(f"✅ README文档已创建")
            print(f"✅ 广东省爬虫已就绪")
            
            print(f"\n📋 下一步操作建议:")
            print(f"1. 运行广东省爬虫: python src/guangdong_datacenter_crawler.py")
            print(f"2. 查看项目文档: docs/README.md")
            print(f"3. 查看数据输出: data/guangdong/")
            
        except Exception as e:
            print(f"❌ 项目整理过程中出错: {e}")
            import traceback
            traceback.print_exc()

def main():
    """主函数"""
    print("📁 数据中心爬虫项目整理工具")
    print("🎯 目标：将项目重构为专门爬取广东省的数据中心爬虫")
    
    organizer = ProjectOrganizer()
    organizer.run_full_organization()

if __name__ == "__main__":
    main()
