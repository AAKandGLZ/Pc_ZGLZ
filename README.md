# 数据中心爬虫使用说明

## 项目简介

本项目用于爬取 datacenters.com 网站上四川省、云南省、贵州省的数据中心位置信息，包括坐标和名称。

## 文件说明

1. **datacenter_crawler.py** - 完整版爬虫，功能丰富
2. **simple_datacenter_crawler.py** - 简化版爬虫，专门针对gmp-advanced-marker元素
3. **requirements.txt** - Python依赖包列表
4. **install.bat** - Windows安装脚本
5. **README.md** - 本说明文件

## 安装步骤

### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 2. 安装Chrome浏览器

确保系统已安装Google Chrome浏览器

### 3. 安装ChromeDriver

#### 方法一：手动安装
1. 访问 https://chromedriver.chromium.org/
2. 下载与Chrome版本对应的ChromeDriver
3. 将chromedriver.exe放入系统PATH中

#### 方法二：自动管理
```bash
pip install webdriver-manager
```

### 4. 运行爬虫

```bash
# 运行简化版（推荐）
python simple_datacenter_crawler.py

# 或运行完整版
python datacenter_crawler.py
```

## 爬取目标

- **四川省**: https://www.datacenters.com/locations/china/sichuan-sheng
- **云南省**: https://www.datacenters.com/locations/china/yunnan-sheng  
- **贵州省**: https://www.datacenters.com/locations/china/guizhou-sheng

## 输出文件

爬取完成后会生成以下文件：

- `datacenter_results.csv` - CSV格式的数据中心信息
- `datacenter_results.json` - JSON格式的数据中心信息

## 数据结构

每个数据中心包含以下字段：

```json
{
  "index": 1,
  "latitude": 31.1978662,
  "longitude": 107.5090321,
  "name": "四川省数据中心",
  "address": "China, Sichuan, Neijiang, Dongxing Qu, 西林大道",
  "province": "四川省",
  "source_url": "https://www.datacenters.com/locations/china/sichuan-sheng",
  "position_raw": "31.1978662,107.5090321"
}
```

## 注意事项

1. 爬取过程中浏览器会自动打开，请不要手动关闭
2. 网络连接需要稳定，爬取过程可能需要几分钟
3. 如果遇到访问限制，可以调整爬取间隔时间
4. 首次运行可能需要下载浏览器驱动

## 故障排除

### 问题1：selenium模块未找到
```bash
pip install selenium
```

### 问题2：ChromeDriver版本不匹配
1. 查看Chrome版本：在地址栏输入 `chrome://version/`
2. 下载对应版本的ChromeDriver

### 问题3：网页加载失败
- 检查网络连接
- 尝试更换网络环境
- 增加页面加载等待时间

### 问题4：找不到地图标记
- 网站可能更新了HTML结构
- 可以修改选择器策略
- 尝试增加等待时间

## 技术原理

1. 使用Selenium自动化浏览器访问目标网页
2. 等待地图加载完成
3. 查找所有`gmp-advanced-marker`元素
4. 从`position`属性中提取坐标信息
5. 通过点击标记获取名称和地址信息
6. 将数据保存为CSV和JSON格式

## 扩展功能

如需增加其他省份，可在代码中修改`provinces_urls`字典：

```python
self.provinces_urls = {
    "四川省": "https://www.datacenters.com/locations/china/sichuan-sheng",
    "云南省": "https://www.datacenters.com/locations/china/yunnan-sheng", 
    "贵州省": "https://www.datacenters.com/locations/china/guizhou-sheng",
    "新省份": "https://www.datacenters.com/locations/china/new-province"
}
```

## 法律声明

本工具仅用于学习和研究目的，请遵守网站的robots.txt协议和使用条款，不要过度频繁访问以免给服务器造成负担。
