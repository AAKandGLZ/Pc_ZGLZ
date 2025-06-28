#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上海数据中心完整翻页分析工具
分析网站的翻页机制并确保获取所有54个数据中心
"""

import requests
import re
import json
import time
import os
from datetime import datetime
from bs4 import BeautifulSoup

class ShanghaiPaginationAnalyzer:
    def __init__(self):
        self.base_url = "https://www.datacenters.com/locations/china/shanghai"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.datacenters.com/',
            'Cache-Control': 'no-cache',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        self.all_datacenters = []
        self.page_data = {}
        
        # 创建输出目录
        os.makedirs("html_sources/shanghai", exist_ok=True)
        os.makedirs("data/shanghai", exist_ok=True)
    
    def analyze_main_page(self):
        """分析主页面，了解翻页结构"""
        print("🔍 分析主页面结构...")
        
        try:
            response = self.session.get(self.base_url, timeout=30)
            if response.status_code == 200:
                # 保存页面
                with open("html_sources/shanghai/main_analysis.html", 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找分页信息
                pagination_info = self.extract_pagination_info(soup, response.text)
                
                # 查找数据容器
                data_containers = self.find_data_containers(soup)
                
                # 查找AJAX端点
                ajax_endpoints = self.find_ajax_endpoints(response.text)
                
                print(f"✅ 主页面分析完成")
                print(f"  翻页信息: {pagination_info}")
                print(f"  数据容器: {len(data_containers)} 个")
                print(f"  AJAX端点: {len(ajax_endpoints)} 个")
                
                return {
                    'pagination': pagination_info,
                    'containers': data_containers,
                    'ajax': ajax_endpoints,
                    'content': response.text
                }
            else:
                print(f"❌ 主页面请求失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 主页面分析错误: {e}")
            return None
    
    def extract_pagination_info(self, soup, content):
        """提取分页信息"""
        pagination_info = {
            'total_pages': 0,
            'current_page': 1,
            'items_per_page': 0,
            'total_items': 0,
            'pagination_type': 'unknown'
        }
        
        # 查找分页相关的文本和元素
        pagination_patterns = [
            r'(?:Page|页面)\s+(\d+)\s+of\s+(\d+)',
            r'(\d+)\s*-\s*(\d+)\s+of\s+(\d+)',
            r'Showing\s+(\d+)\s*-\s*(\d+)\s+of\s+(\d+)',
            r'"totalPages":\s*(\d+)',
            r'"currentPage":\s*(\d+)',
            r'"totalResults":\s*(\d+)',
            r'"itemsPerPage":\s*(\d+)',
        ]
        
        for pattern in pagination_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                print(f"  找到分页模式: {pattern} -> {matches}")
        
        # 查找分页按钮
        pagination_elements = soup.find_all(['a', 'button'], text=re.compile(r'(Next|Previous|下一页|上一页|\d+)', re.IGNORECASE))
        if pagination_elements:
            print(f"  找到分页按钮: {len(pagination_elements)} 个")
        
        # 查找总数信息
        total_patterns = [
            r'(\d+)\s*(?:data centers?|数据中心)',
            r'Total:\s*(\d+)',
            r'Found\s+(\d+)',
        ]
        
        for pattern in total_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                total = int(matches[0])
                pagination_info['total_items'] = total
                print(f"  找到总数: {total}")
                break
        
        return pagination_info
    
    def find_data_containers(self, soup):
        """查找数据容器"""
        containers = []
        
        # 常见的数据容器选择器
        container_selectors = [
            '.datacenter-item',
            '.location-item',
            '.facility-item',
            '[data-lat]',
            '[data-longitude]',
            '.result-item',
            '.listing-item',
        ]
        
        for selector in container_selectors:
            elements = soup.select(selector)
            if elements:
                containers.extend(elements)
                print(f"  找到容器 {selector}: {len(elements)} 个")
        
        return containers
    
    def find_ajax_endpoints(self, content):
        """查找AJAX端点"""
        endpoints = []
        
        # AJAX端点模式
        ajax_patterns = [
            r'["\']([^"\']*api[^"\']*)["\']',
            r'["\']([^"\']*ajax[^"\']*)["\']',
            r'url:\s*["\']([^"\']+)["\']',
            r'fetch\(["\']([^"\']+)["\']',
        ]
        
        for pattern in ajax_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if 'datacenter' in match.lower() or 'location' in match.lower():
                    endpoints.append(match)
        
        return list(set(endpoints))
    
    def try_different_pagination_methods(self):
        """尝试不同的翻页方法"""
        print("🔄 尝试不同的翻页方法...")
        
        all_results = []
        methods_tried = []
        
        # 方法1: URL参数翻页
        print("  方法1: URL参数翻页")
        results1 = self.try_url_pagination()
        if results1:
            all_results.extend(results1)
            methods_tried.append("URL参数翻页")
        
        # 方法2: AJAX翻页
        print("  方法2: AJAX翻页")
        results2 = self.try_ajax_pagination()
        if results2:
            all_results.extend(results2)
            methods_tried.append("AJAX翻页")
        
        # 方法3: 表单提交翻页
        print("  方法3: 表单提交翻页")
        results3 = self.try_form_pagination()
        if results3:
            all_results.extend(results3)
            methods_tried.append("表单提交翻页")
        
        # 方法4: 直接URL构造
        print("  方法4: 直接URL构造")
        results4 = self.try_direct_urls()
        if results4:
            all_results.extend(results4)
            methods_tried.append("直接URL构造")
        
        print(f"✅ 尝试的方法: {methods_tried}")
        print(f"✅ 总获取数据: {len(all_results)} 个")
        
        return all_results, methods_tried
    
    def try_url_pagination(self):
        """尝试URL参数翻页"""
        results = []
        
        url_patterns = [
            f"{self.base_url}?page={{}}",
            f"{self.base_url}?p={{}}",
            f"{self.base_url}?offset={{}}",
            f"{self.base_url}/page/{{}}",
            f"{self.base_url}?start={{}}",
            f"{self.base_url}?from={{}}",
        ]
        
        for pattern in url_patterns:
            print(f"    尝试模式: {pattern.replace('{}', 'N')}")
            
            for page in range(1, 10):  # 尝试前9页
                url = pattern.format(page)
                
                try:
                    response = self.session.get(url, timeout=20)
                    if response.status_code == 200:
                        # 保存页面
                        page_file = f"html_sources/shanghai/page_{page}_pattern_{pattern.split('?')[-1].split('=')[0]}.html"
                        with open(page_file, 'w', encoding='utf-8') as f:
                            f.write(response.text)
                        
                        # 提取数据
                        page_results = self.extract_datacenters(response.text, f"page_{page}")
                        
                        if page_results:
                            results.extend(page_results)
                            print(f"      页面 {page}: 找到 {len(page_results)} 个数据中心")
                        else:
                            if page > 1:  # 第一页没数据可能是模式错误，其他页没数据可能是结束了
                                break
                    
                    time.sleep(1)  # 避免请求过快
                    
                except Exception as e:
                    print(f"      页面 {page} 错误: {e}")
                    if page > 1:
                        break
            
            if results:
                print(f"    模式 {pattern.replace('{}', 'N')} 成功，共获取 {len(results)} 个")
                break  # 找到工作的模式就停止
        
        return results
    
    def try_ajax_pagination(self):
        """尝试AJAX翻页"""
        results = []
        
        # 常见的AJAX端点
        ajax_endpoints = [
            "/api/datacenters",
            "/ajax/locations",
            "/search/datacenters",
            "/locations/shanghai/data",
        ]
        
        for endpoint in ajax_endpoints:
            url = f"https://www.datacenters.com{endpoint}"
            
            try:
                # 尝试不同的参数
                params_list = [
                    {'location': 'shanghai', 'page': 1},
                    {'city': 'shanghai', 'page': 1},
                    {'query': 'shanghai', 'offset': 0},
                    {'lat': 31.2304, 'lng': 121.4737, 'radius': 50},
                ]
                
                for params in params_list:
                    response = self.session.get(url, params=params, timeout=20)
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            if isinstance(data, list) and data:
                                results.extend(self.process_json_data(data, "ajax"))
                                print(f"    AJAX端点 {endpoint} 成功")
                                return results
                        except:
                            # 可能返回的是HTML
                            page_results = self.extract_datacenters(response.text, "ajax")
                            if page_results:
                                results.extend(page_results)
                                return results
                
            except Exception as e:
                print(f"    AJAX端点 {endpoint} 错误: {e}")
        
        return results
    
    def try_form_pagination(self):
        """尝试表单提交翻页"""
        results = []
        
        try:
            # 获取主页面找到表单
            response = self.session.get(self.base_url, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找搜索或分页表单
                forms = soup.find_all('form')
                for form in forms:
                    action = form.get('action', '')
                    method = form.get('method', 'GET').upper()
                    
                    if 'search' in action.lower() or 'location' in action.lower():
                        # 提取表单数据
                        form_data = {}
                        for input_elem in form.find_all(['input', 'select']):
                            name = input_elem.get('name')
                            value = input_elem.get('value', '')
                            if name:
                                form_data[name] = value
                        
                        # 添加上海相关参数
                        form_data.update({
                            'location': 'shanghai',
                            'city': 'shanghai',
                            'country': 'china',
                            'page': '1'
                        })
                        
                        # 提交表单
                        if method == 'POST':
                            form_response = self.session.post(f"https://www.datacenters.com{action}", data=form_data, timeout=20)
                        else:
                            form_response = self.session.get(f"https://www.datacenters.com{action}", params=form_data, timeout=20)
                        
                        if form_response.status_code == 200:
                            page_results = self.extract_datacenters(form_response.text, "form")
                            if page_results:
                                results.extend(page_results)
                                print(f"    表单提交成功，获取 {len(page_results)} 个")
        
        except Exception as e:
            print(f"    表单提交错误: {e}")
        
        return results
    
    def try_direct_urls(self):
        """尝试直接构造URL"""
        results = []
        
        # 尝试不同的URL构造方式
        direct_urls = [
            "https://www.datacenters.com/locations/china-shanghai",
            "https://www.datacenters.com/shanghai",
            "https://www.datacenters.com/search?location=shanghai",
            "https://www.datacenters.com/search?q=shanghai",
            "https://www.datacenters.com/china/shanghai/all",
            "https://www.datacenters.com/locations/shanghai/list",
        ]
        
        for url in direct_urls:
            try:
                response = self.session.get(url, timeout=20)
                if response.status_code == 200:
                    page_results = self.extract_datacenters(response.text, f"direct_{url.split('/')[-1]}")
                    if page_results:
                        results.extend(page_results)
                        print(f"    直接URL {url} 成功，获取 {len(page_results)} 个")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"    直接URL {url} 错误: {e}")
        
        return results
    
    def extract_datacenters(self, content, source):
        """从内容中提取数据中心信息"""
        results = []
        
        # JavaScript数据提取
        js_patterns = [
            r'"latitude":\s*([\d\.-]+).*?"longitude":\s*([\d\.-]+).*?"name":\s*"([^"]*)"',
            r'"lat":\s*([\d\.-]+).*?"lng":\s*([\d\.-]+).*?"title":\s*"([^"]*)"',
            r'position:\s*\[([\d\.-]+),\s*([\d\.-]+)\].*?name:\s*"([^"]*)"',
        ]
        
        for pattern in js_patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    lat, lng, name = float(match[0]), float(match[1]), match[2].strip()
                    
                    # 验证坐标是否在上海范围内
                    if 30.6 <= lat <= 31.9 and 120.8 <= lng <= 122.2:
                        results.append({
                            'name': name,
                            'latitude': lat,
                            'longitude': lng,
                            'source': source,
                            'province': '上海市',
                            'city': '上海市',
                            'coordinates': f"{lat},{lng}",
                            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                except ValueError:
                    continue
        
        # HTML结构化数据提取
        soup = BeautifulSoup(content, 'html.parser')
        
        # 查找带坐标属性的元素
        coord_elements = soup.find_all(attrs={'data-lat': True}) + soup.find_all(attrs={'data-latitude': True})
        for elem in coord_elements:
            try:
                lat = float(elem.get('data-lat') or elem.get('data-latitude'))
                lng = float(elem.get('data-lng') or elem.get('data-longitude'))
                
                name = (elem.get('title') or 
                       elem.get('data-name') or 
                       elem.get_text(strip=True) or 
                       f"上海数据中心_{len(results)+1}")
                
                if 30.6 <= lat <= 31.9 and 120.8 <= lng <= 122.2:
                    results.append({
                        'name': name,
                        'latitude': lat,
                        'longitude': lng,
                        'source': source,
                        'province': '上海市',
                        'city': '上海市',
                        'coordinates': f"{lat},{lng}",
                        'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            except (ValueError, TypeError):
                continue
        
        return results
    
    def process_json_data(self, data, source):
        """处理JSON数据"""
        results = []
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    lat = item.get('latitude') or item.get('lat')
                    lng = item.get('longitude') or item.get('lng')
                    name = item.get('name') or item.get('title') or f"数据中心_{len(results)+1}"
                    
                    if lat and lng:
                        try:
                            lat, lng = float(lat), float(lng)
                            if 30.6 <= lat <= 31.9 and 120.8 <= lng <= 122.2:
                                results.append({
                                    'name': name,
                                    'latitude': lat,
                                    'longitude': lng,
                                    'source': source,
                                    'province': '上海市',
                                    'city': '上海市',
                                    'coordinates': f"{lat},{lng}",
                                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                })
                        except ValueError:
                            continue
        
        return results
    
    def run_complete_analysis(self):
        """运行完整分析"""
        print("🚀 上海数据中心完整翻页分析启动")
        print("🎯 目标：分析翻页机制并获取所有54个数据中心")
        print("="*70)
        
        # 1. 分析主页面
        main_analysis = self.analyze_main_page()
        
        # 2. 尝试不同翻页方法
        all_results, methods = self.try_different_pagination_methods()
        
        # 3. 去重
        unique_results = self.deduplicate_results(all_results)
        
        # 4. 保存结果
        if unique_results:
            self.save_analysis_results(unique_results, methods, main_analysis)
        
        print(f"\n{'='*70}")
        print(f"📊 完整分析结果:")
        print(f"  总数据中心: {len(unique_results)} 个")
        print(f"  成功方法: {methods}")
        print(f"  目标达成: {'✅' if len(unique_results) >= 54 else '❌'} ({len(unique_results)}/54)")
        
        return unique_results
    
    def deduplicate_results(self, results):
        """去重结果"""
        print(f"🔄 数据去重: {len(results)} -> ", end="")
        
        unique_results = []
        seen_coords = set()
        
        for result in results:
            # 基于坐标去重（精确到小数点后5位）
            coord_key = (round(result['latitude'], 5), round(result['longitude'], 5))
            
            if coord_key not in seen_coords:
                seen_coords.add(coord_key)
                result['index'] = len(unique_results) + 1
                unique_results.append(result)
        
        print(f"{len(unique_results)}")
        return unique_results
    
    def save_analysis_results(self, results, methods, main_analysis):
        """保存分析结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存JSON数据
        json_file = f"data/shanghai/上海数据中心完整翻页_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"✅ 数据已保存: {json_file}")
        
        # 生成分析报告
        report_file = f"data/shanghai/翻页分析报告_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("上海数据中心完整翻页分析报告\n")
            f.write("="*60 + "\n\n")
            
            f.write(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"目标数量: 54个数据中心\n")
            f.write(f"实际获取: {len(results)}个数据中心\n")
            f.write(f"达成率: {len(results)/54*100:.1f}%\n\n")
            
            f.write("成功的翻页方法:\n")
            f.write("-"*30 + "\n")
            for method in methods:
                f.write(f"✅ {method}\n")
            f.write("\n")
            
            if main_analysis:
                f.write("主页面分析结果:\n")
                f.write("-"*30 + "\n")
                f.write(f"翻页信息: {main_analysis.get('pagination', {})}\n")
                f.write(f"数据容器: {len(main_analysis.get('containers', []))}个\n")
                f.write(f"AJAX端点: {len(main_analysis.get('ajax', []))}个\n\n")
            
            f.write("获取的数据中心列表:\n")
            f.write("-"*30 + "\n")
            for i, dc in enumerate(results, 1):
                f.write(f"{i:2d}. {dc['name']}\n")
                f.write(f"    坐标: ({dc['latitude']:.6f}, {dc['longitude']:.6f})\n")
                f.write(f"    来源: {dc['source']}\n\n")
        
        print(f"✅ 报告已保存: {report_file}")

def main():
    """主函数"""
    print("🔍 上海数据中心完整翻页分析工具")
    print("🎯 分析翻页机制，确保获取所有54个数据中心")
    
    analyzer = ShanghaiPaginationAnalyzer()
    
    try:
        results = analyzer.run_complete_analysis()
        
        if len(results) >= 54:
            print(f"\n🎉 任务完成！成功获取 {len(results)} 个数据中心")
        else:
            print(f"\n⚠️ 需要进一步优化：目前获取 {len(results)} 个，目标 54 个")
            
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断分析")
    except Exception as e:
        print(f"❌ 分析过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
