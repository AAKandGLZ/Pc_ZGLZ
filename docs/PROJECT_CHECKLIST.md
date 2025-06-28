# 项目文件清单

## 📁 核心代码文件
- [x] `final_datacenter_crawler.py` - 主要爬虫脚本（推荐）
- [x] `simple_datacenter_crawler.py` - 简化版爬虫
- [x] `view_results.py` - 结果查看工具
- [x] `extract_coordinates.py` - 坐标提取工具

## 📄 配置文件
- [x] `requirements.txt` - Python依赖包列表
- [x] `.gitignore` - Git忽略文件配置
- [x] `README.md` - 项目说明文档
- [x] `PUBLISH.md` - 发布指南
- [x] `LICENSE` - 许可证文件

## 📊 数据文件
- [x] `重新爬取完整三省数据中心坐标.json` - 最终数据结果（34个数据中心）
- [x] `重新爬取完整三省数据中心坐标.csv` - CSV格式数据
- [x] `完整三省数据中心坐标.json` - 备份数据

## 📈 报告文件
- [x] `最终完整数据中心报告.txt` - 详细分析报告
- [x] `项目完成报告.md` - 项目总结
- [x] `完整数据摘要.md` - 数据摘要

## 🔧 辅助脚本
- [x] `install.bat` - Windows一键安装脚本
- [x] `run_crawler.bat` - Windows运行脚本
- [x] `test_environment.py` - 环境测试脚本

## ❌ 排除文件（.gitignore已配置）
- 临时HTML文件 (`*_page.html`, `*_source.html`)
- 浏览器驱动 (`chromedriver.exe`)
- 截图文件 (`*.png`, `*.jpg`)
- Python缓存 (`__pycache__/`)
- 虚拟环境 (`venv/`, `env/`)

## 🎯 核心数据统计
- **四川省**: 27个数据中心
- **云南省**: 2个数据中心
- **贵州省**: 5个数据中心
- **总计**: 34个数据中心位置信息

## 📝 使用建议
1. 主要使用 `final_datacenter_crawler.py` 进行数据采集
2. 参考 `README.md` 了解详细使用方法
3. 查看 `重新爬取完整三省数据中心坐标.json` 获取最新数据
4. 阅读 `最终完整数据中心报告.txt` 了解数据质量分析

## 🚀 准备发布状态
✅ 项目已准备好发布到 GitHub 组织工作空间
