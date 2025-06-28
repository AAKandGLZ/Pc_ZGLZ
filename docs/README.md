# 数据中心爬虫项目

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

### 2025-06-20
- 创建广东省专用数据中心爬虫
- 重构项目目录结构
- 添加自动化项目整理功能
- 完善文档和使用说明

## 许可证
本项目仅供学习和研究使用。

## 联系方式
如有问题请提交Issue或联系项目维护者。
