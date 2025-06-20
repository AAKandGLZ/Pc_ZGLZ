# 中国西南三省数据中心位置爬虫

## 🎯 项目简介

本项目用于爬取 [datacenters.com](https://www.datacenters.com) 网站上**四川省**、**云南省**、**贵州省**的数据中心位置信息，包括精确坐标、名称等详细信息。

## 📊 爬取结果

- **四川省**: 27个数据中心
- **云南省**: 2个数据中心  
- **贵州省**: 5个数据中心
- **总计**: 34个数据中心

## 🚀 快速开始

### 1. 环境要求

- Python 3.7+
- Google Chrome 浏览器
- Windows/Linux/macOS

### 2. 安装依赖

```bash
# 克隆项目
git clone https://github.com/AAKandGLZ/Pc_ZGLZ.git
cd Pc_ZGLZ

# 安装Python依赖
pip install -r requirements.txt
```

### 3. 运行爬虫

**推荐使用最终版爬虫**（速度快，准确性高）：
```bash
python final_datacenter_crawler.py
```

**或使用简化版Selenium爬虫**：
```bash
python simple_datacenter_crawler.py
```

### 4. 查看结果

```bash
# 查看爬取结果
python view_results.py

# 数据文件位置
重新爬取完整三省数据中心坐标.json    # JSON格式
重新爬取完整三省数据中心坐标.csv     # CSV格式
```

## 📁 项目结构

```
爬虫/
├── 📄 README.md                                    # 项目说明文档
├── 📄 requirements.txt                             # Python依赖包
├── 📄 .gitignore                                   # Git忽略文件
├── 
├── 🔧 主要爬虫脚本/
│   ├── final_datacenter_crawler.py                # ⭐ 最终版爬虫（推荐）
│   ├── simple_datacenter_crawler.py               # 简化版Selenium爬虫
│   ├── auto_datacenter_crawler.py                 # 自动化版本
│   └── complete_datacenter_crawler.py             # 完整版爬虫
├── 
├── 🛠️ 辅助工具/
│   ├── analyze_website.py                         # 网站结构分析
│   ├── extract_coordinates.py                     # 坐标提取工具
│   ├── view_results.py                            # 结果查看器
│   └── test_environment.py                        # 环境测试工具
├── 
├── 📊 数据文件/
│   ├── 重新爬取完整三省数据中心坐标.json           # 完整数据（JSON）
│   ├── 重新爬取完整三省数据中心坐标.csv            # 完整数据（CSV）
│   ├── 最终完整数据中心报告.txt                    # 详细统计报告
│   └── 完整数据摘要.md                             # 数据摘要
├── 
├── 📝 文档报告/
│   ├── 项目完成报告.md                             # 项目完成报告
│   └── 详细检查结果汇总.json                       # 检查结果汇总
└── 
└── 🔧 批处理脚本/
    ├── install.bat                                 # Windows安装脚本
    └── run_crawler.bat                             # 快速启动脚本
```

## 💻 使用方法

### 基础爬取

```python
from final_datacenter_crawler import DataCenterCrawler

# 创建爬虫实例
crawler = DataCenterCrawler()

# 运行爬虫
crawler.run()

# 查看结果
results = crawler.get_results()
print(f"爬取到 {len(results)} 个数据中心")
```

### 分析网站结构

```bash
python analyze_website.py
```

### 测试环境

```bash
python test_environment.py
```

## 📈 数据格式

### JSON格式
```json
{
  "province": "四川省",
  "latitude": 30.6508899,
  "longitude": 104.07572,
  "name": "CTU1 Sichuan Sheng Data Center",
  "source": "四川省-sichuan-sheng",
  "coordinates": "30.6508899,104.07572",
  "index": 1
}
```

### CSV格式
```csv
province,latitude,longitude,name,source,coordinates,index
四川省,30.6508899,104.07572,CTU1 Sichuan Sheng Data Center,四川省-sichuan-sheng,"30.6508899,104.07572",1
```

## 🎯 核心特性

- **多策略爬取**: 支持HTML解析和Selenium两种方式
- **智能去重**: 自动识别和合并重复数据
- **坐标验证**: 验证坐标格式和合理性
- **多格式输出**: 支持JSON、CSV格式导出
- **详细日志**: 完整的爬取过程记录
- **错误处理**: 完善的异常处理机制

## 🛠️ 技术栈

- **Python 3.7+**
- **Selenium**: 浏览器自动化
- **Beautiful Soup**: HTML解析
- **Pandas**: 数据处理
- **Requests**: HTTP请求
- **ChromeDriver**: Chrome浏览器驱动

## 📋 依赖包

```
selenium>=4.0.0
webdriver-manager>=4.0.0
requests>=2.25.0
pandas>=1.3.0
beautifulsoup4>=4.9.0
lxml>=4.6.0
openpyxl>=3.0.0
```

## 🚨 注意事项

1. **浏览器要求**: 需要安装Google Chrome浏览器
2. **网络要求**: 需要能够访问 datacenters.com 网站
3. **运行时间**: 完整爬取约需要3-5分钟
4. **数据时效**: 数据来源于网站，可能存在时效性
5. **使用规范**: 请遵守网站的robots.txt和使用条款

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

如有问题或建议，请创建 Issue 或直接联系项目维护者。

---

**⚠️ 免责声明**: 本项目仅用于学习和研究目的，请遵守相关网站的使用条款和法律法规。
