#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JavaScript翻页检测和爬取工具
不依赖WebDriver，使用requests-html或其他方法处理JavaScript翻页
"""

import requests
import json
import time
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup
import threading

class SmartPaginationCrawler:
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
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        self.all_datacenters = []
        self.page_data = {}
        
        # 创建输出目录
        os.makedirs("data/shanghai", exist_ok=True)
        os.makedirs("html_sources/shanghai", exist_ok=True)
    
    def analyze_page_structure(self):
        """分析页面结构，找出JavaScript翻页机制"""
        print("🔍 分析页面的JavaScript翻页机制...")
        
        try:
            response = self.session.get(self.base_url, timeout=30)
            if response.status_code != 200:
                print(f"❌ 页面请求失败: {response.status_code}")
                return None
            
            # 保存原始页面
            with open("html_sources/shanghai/original_page.html", 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            analysis = {
                'pagination_info': self.extract_pagination_info(response.text, soup),
                'ajax_endpoints': self.find_ajax_endpoints(response.text),
                'javascript_functions': self.find_javascript_pagination(response.text),
                'data_structure': self.analyze_data_structure(response.text)
            }
            
            return analysis
            
        except Exception as e:
            print(f"❌ 页面分析失败: {e}")
            return None
    
    def extract_pagination_info(self, content, soup):
        """提取分页信息"""
        pagination_info = {
            'total_pages': 0,
            'current_page': 1,
            'items_per_page': 0,
            'total_items': 0,
            'pagination_method': 'unknown'
        }
        
        # 从JavaScript变量中提取分页信息
        js_patterns = [
            r'"totalPages":\s*(\d+)',
            r'"pageCount":\s*(\d+)', 
            r'"currentPage":\s*(\d+)',
            r'"page":\s*(\d+)',
            r'totalPages\s*[:=]\s*(\d+)',
            r'pageCount\s*[:=]\s*(\d+)',
            r'var\s+totalPages\s*=\s*(\d+)',
            r'let\s+totalPages\s*=\s*(\d+)',
            r'const\s+totalPages\s*=\s*(\d+)',
        ]
        
        for pattern in js_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                try:
                    value = int(matches[0])
                    if 'total' in pattern.lower() or 'count' in pattern.lower():
                        pagination_info['total_pages'] = value
                        print(f"  检测到总页数: {value}")
                    elif 'current' in pattern.lower():
                        pagination_info['current_page'] = value
                        print(f"  检测到当前页: {value}")
                except:
                    continue
        
        # 查找分页按钮
        pagination_elements = soup.find_all(['a', 'button'], string=re.compile(r'\d+'))
        page_numbers = []
        for elem in pagination_elements:
            text = elem.get_text(strip=True)
            if text.isdigit():
                page_numbers.append(int(text))
        
        if page_numbers:
            pagination_info['total_pages'] = max(pagination_info['total_pages'], max(page_numbers))
            print(f"  从按钮检测到页数: {max(page_numbers)}")
        
        # 查找数据项总数
        total_patterns = [
            r'(\d+)\s*(?:results?|数据中心|data\s*centers?)',
            r'(?:Total|共)\s*[:：]?\s*(\d+)',
            r'(?:Showing|显示)\s+\d+\s*-\s*\d+\s+(?:of|共)\s+(\d+)',
        ]
        
        for pattern in total_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                try:
                    total = int(matches[0])
                    pagination_info['total_items'] = total
                    print(f"  检测到数据总数: {total}")
                    break
                except:
                    continue
        
        return pagination_info
    
    def find_ajax_endpoints(self, content):
        """查找AJAX端点"""
        endpoints = []
        
        ajax_patterns = [
            r'url\s*:\s*["\']([^"\']*(?:page|data|search|load)[^"\']*)["\']',
            r'fetch\s*\(\s*["\']([^"\']+)["\']',
            r'\.get\s*\(\s*["\']([^"\']+)["\']',
            r'\.post\s*\(\s*["\']([^"\']+)["\']',
            r'ajax\s*\(\s*["\']([^"\']+)["\']',
            r'loadUrl\s*:\s*["\']([^"\']+)["\']',
        ]
        
        for pattern in ajax_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if any(keyword in match.lower() for keyword in ['datacenter', 'location', 'search', 'api']):
                    endpoints.append(match)
        
        unique_endpoints = list(set(endpoints))
        if unique_endpoints:
            print(f"  找到AJAX端点: {unique_endpoints}")
        
        return unique_endpoints
    
    def find_javascript_pagination(self, content):
        """查找JavaScript翻页函数"""
        functions = []
        
        function_patterns = [
            r'function\s+(\w*(?:page|load|show|navigate)\w*)\s*\(',
            r'(\w*(?:page|load|show|navigate)\w*)\s*:\s*function',
            r'(\w*(?:page|load|show|navigate)\w*)\s*=\s*function',
            r'(\w*(?:page|load|show|navigate)\w*)\s*=>\s*{',
        ]
        
        for pattern in function_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            functions.extend(matches)
        
        unique_functions = list(set(functions))
        if unique_functions:
            print(f"  找到翻页函数: {unique_functions}")
        
        return unique_functions
    
    def analyze_data_structure(self, content):
        """分析数据结构"""
        data_info = {
            'data_variables': [],
            'data_arrays': [],
            'coordinate_patterns': []
        }
        
        # 查找数据变量
        var_patterns = [
            r'(?:var|let|const)\s+(\w*(?:data|center|location|marker)\w*)\s*=',
            r'window\.(\w*(?:data|center|location|marker)\w*)\s*=',
        ]
        
        for pattern in var_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            data_info['data_variables'].extend(matches)
        
        # 查找数组数据
        array_patterns = [
            r'(\w*(?:data|center|location|marker)\w*)\s*=\s*\[',
            r'(\w*(?:data|center|location|marker)\w*)\s*:\s*\[',
        ]
        
        for pattern in array_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            data_info['data_arrays'].extend(matches)
        
        if data_info['data_variables']:
            print(f"  找到数据变量: {list(set(data_info['data_variables']))}")
        if data_info['data_arrays']:
            print(f"  找到数据数组: {list(set(data_info['data_arrays']))}")
        
        return data_info
    
    def try_different_pagination_approaches(self):
        """尝试不同的翻页方法"""
        print("🔄 尝试不同的翻页方法获取完整数据...")
        
        all_results = []
        successful_methods = []
        
        # 方法1: AJAX请求翻页
        print("  方法1: AJAX请求翻页")
        ajax_results = self.try_ajax_pagination()
        if ajax_results:
            all_results.extend(ajax_results)
            successful_methods.append("AJAX翻页")
        
        # 方法2: 表单POST翻页
        print("  方法2: 表单POST翻页")
        post_results = self.try_post_pagination()
        if post_results:
            all_results.extend(post_results)
            successful_methods.append("POST翻页")
        
        # 方法3: 构造特殊参数
        print("  方法3: 构造特殊参数")
        param_results = self.try_parameter_pagination()
        if param_results:
            all_results.extend(param_results)
            successful_methods.append("参数翻页")
        
        # 方法4: 模拟JavaScript请求
        print("  方法4: 模拟JavaScript请求")
        js_results = self.try_javascript_simulation()
        if js_results:
            all_results.extend(js_results)
            successful_methods.append("JS模拟")
        
        return all_results, successful_methods
    
    def try_ajax_pagination(self):
        """尝试AJAX翻页"""
        results = []
        
        # 常见的AJAX端点路径
        ajax_paths = [
            "/api/locations",
            "/api/datacenters", 
            "/search/locations",
            "/locations/data",
            "/ajax/search",
            "/data/locations.json",
        ]
        
        base_domain = "https://www.datacenters.com"
        
        for path in ajax_paths:
            url = base_domain + path
            
            # 尝试不同的参数组合
            param_combinations = [
                {'location': 'shanghai', 'page': 1},
                {'location': 'shanghai', 'page': 2},
                {'city': 'shanghai', 'page': 1},
                {'city': 'shanghai', 'page': 2},
                {'q': 'shanghai', 'offset': 0, 'limit': 50},
                {'search': 'shanghai', 'start': 0, 'count': 50},
                {'query': 'shanghai', 'pageNumber': 1},
                {'query': 'shanghai', 'pageNumber': 2},
            ]
            
            for params in param_combinations:
                try:
                    response = self.session.get(url, params=params, timeout=20)
                    if response.status_code == 200:
                        # 尝试解析为JSON
                        try:
                            data = response.json()
                            if isinstance(data, list) and data:
                                page_results = self.process_json_response(data, f"ajax_{path.split('/')[-1]}")
                                if page_results:
                                    results.extend(page_results)
                                    print(f"    AJAX成功: {url} -> {len(page_results)} 个")
                        except:
                            # 可能是HTML响应
                            html_results = self.extract_from_html(response.text, f"ajax_{path.split('/')[-1]}")
                            if html_results:
                                results.extend(html_results)
                                print(f"    AJAX HTML成功: {url} -> {len(html_results)} 个")
                    
                    time.sleep(1)
                    
                except Exception as e:
                    continue
        
        return results
    
    def try_post_pagination(self):
        """尝试POST翻页"""
        results = []
        
        try:
            # 首先获取页面中的表单信息
            response = self.session.get(self.base_url, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找表单
                forms = soup.find_all('form')
                for form in forms:
                    action = form.get('action', '')
                    method = form.get('method', 'GET').upper()
                    
                    if method == 'POST' or 'search' in action.lower():
                        # 构造表单数据
                        form_data = {}
                        
                        # 提取现有的input值
                        for input_elem in form.find_all('input'):
                            name = input_elem.get('name')
                            value = input_elem.get('value', '')
                            if name:
                                form_data[name] = value
                        
                        # 添加分页参数
                        page_params = [
                            {'page': 1}, {'page': 2},
                            {'pageNumber': 1}, {'pageNumber': 2},
                            {'offset': 0}, {'offset': 40},
                            {'start': 0}, {'start': 40},
                        ]
                        
                        for page_param in page_params:
                            post_data = {**form_data, **page_param, 'location': 'shanghai', 'city': 'shanghai'}
                            
                            try:
                                if action.startswith('http'):
                                    post_url = action
                                else:
                                    post_url = f"https://www.datacenters.com{action}"
                                
                                post_response = self.session.post(post_url, data=post_data, timeout=20)
                                
                                if post_response.status_code == 200:
                                    page_results = self.extract_from_html(post_response.text, f"post_page_{page_param}")
                                    if page_results:
                                        results.extend(page_results)
                                        print(f"    POST成功: {post_url} -> {len(page_results)} 个")
                                
                                time.sleep(1)
                                
                            except:
                                continue
        
        except Exception as e:
            print(f"    POST方法出错: {e}")
        
        return results
    
    def try_parameter_pagination(self):
        """尝试特殊参数翻页"""
        results = []
        
        # 尝试各种参数组合
        param_sets = [
            # 基础分页参数
            {'page': 1}, {'page': 2}, {'page': 3},
            {'p': 1}, {'p': 2}, {'p': 3},
            
            # 偏移量参数
            {'offset': 0}, {'offset': 40}, {'offset': 80},
            {'start': 0}, {'start': 40}, {'start': 80},
            {'from': 0}, {'from': 40}, {'from': 80},
            
            # 限制参数
            {'limit': 50}, {'limit': 100},
            {'count': 50}, {'count': 100},
            {'size': 50}, {'size': 100},
            
            # 组合参数
            {'page': 1, 'size': 50}, {'page': 2, 'size': 50},
            {'offset': 0, 'limit': 50}, {'offset': 40, 'limit': 50},
            
            # 特殊参数
            {'view': 'all'}, {'view': 'list'}, {'view': 'grid'},
            {'format': 'json'}, {'format': 'xml'},
            {'ajax': '1'}, {'xhr': '1'},
            
            # 搜索相关
            {'search': 'shanghai'}, {'q': 'shanghai'}, {'query': 'shanghai'},
            {'location': 'shanghai'}, {'city': 'shanghai'}, {'country': 'china'},
        ]
        
        for params in param_sets:
            try:
                response = self.session.get(self.base_url, params=params, timeout=20)
                
                if response.status_code == 200:                    # 检查是否获得了不同的数据
                    param_str = str(params).replace(' ', '').replace(':', '').replace(',', '_').replace('{', '').replace('}', '').replace("'", '')
                    page_results = self.extract_from_html(response.text, f"param_{param_str}")
                    
                    if page_results:
                        results.extend(page_results)
                        print(f"    参数成功: {params} -> {len(page_results)} 个")
                
                time.sleep(0.5)
                
            except:
                continue
        
        return results
    
    def try_javascript_simulation(self):
        """尝试模拟JavaScript请求"""
        results = []
        
        try:
            # 获取原始页面
            response = self.session.get(self.base_url, timeout=30)
            if response.status_code != 200:
                return results
            
            # 分析页面中的JavaScript请求
            js_urls = re.findall(r'(?:fetch|\.get|\.post)\s*\(\s*["\']([^"\']+)["\']', response.text, re.IGNORECASE)
            
            for url in js_urls:
                try:
                    # 补全相对URL
                    if url.startswith('/'):
                        full_url = f"https://www.datacenters.com{url}"
                    elif url.startswith('http'):
                        full_url = url
                    else:
                        continue
                    
                    # 添加必要的头部模拟AJAX请求
                    ajax_headers = {
                        **self.headers,
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json, text/javascript, */*; q=0.01',
                    }
                    
                    js_response = self.session.get(full_url, headers=ajax_headers, timeout=20)
                    
                    if js_response.status_code == 200:
                        try:
                            # 尝试解析为JSON
                            data = js_response.json()
                            page_results = self.process_json_response(data, f"js_sim_{url.split('/')[-1]}")
                            if page_results:
                                results.extend(page_results)
                                print(f"    JS模拟成功: {url} -> {len(page_results)} 个")
                        except:
                            # HTML响应
                            page_results = self.extract_from_html(js_response.text, f"js_sim_{url.split('/')[-1]}")
                            if page_results:
                                results.extend(page_results)
                                print(f"    JS模拟HTML成功: {url} -> {len(page_results)} 个")
                    
                    time.sleep(1)
                    
                except:
                    continue
        
        except Exception as e:
            print(f"    JavaScript模拟出错: {e}")
        
        return results
    
    def extract_from_html(self, content, source):
        """从HTML内容中提取数据中心信息"""
        results = []
        
        # JavaScript数据提取
        js_patterns = [
            r'"latitude":\s*([\d\.-]+).*?"longitude":\s*([\d\.-]+).*?"name":\s*"([^"]*)"',
            r'"lat":\s*([\d\.-]+).*?"lng":\s*([\d\.-]+).*?"title":\s*"([^"]*)"',
            r'position:\s*\[([\d\.-]+),\s*([\d\.-]+)\].*?name:\s*"([^"]*)"',
            r'latitude:\s*([\d\.-]+).*?longitude:\s*([\d\.-]+).*?name:\s*["\']([^"\']*)["\']',
        ]
        
        for pattern in js_patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    lat, lng, name = float(match[0]), float(match[1]), match[2].strip()
                    
                    # 验证坐标是否在上海范围内
                    if 30.6 <= lat <= 31.9 and 120.8 <= lng <= 122.2:
                        results.append({
                            'name': name or f"数据中心_{len(results)+1}",
                            'latitude': lat,
                            'longitude': lng,
                            'location': '上海市',
                            'source_page': self.extract_page_number(source),
                            'extraction_method': 'HTML_JS',
                            'source': source,
                            'raw_data': {
                                'name': name,
                                'latitude': lat,
                                'longitude': lng
                            }
                        })
                except ValueError:
                    continue
        
        # HTML结构化数据提取
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # 查找带坐标属性的元素
            coord_elements = (soup.find_all(attrs={'data-lat': True}) + 
                            soup.find_all(attrs={'data-latitude': True}) +
                            soup.find_all(attrs={'lat': True}))
            
            for elem in coord_elements:
                try:
                    lat = float(elem.get('data-lat') or elem.get('data-latitude') or elem.get('lat'))
                    lng = float(elem.get('data-lng') or elem.get('data-longitude') or elem.get('lng'))
                    
                    name = (elem.get('title') or 
                           elem.get('data-name') or 
                           elem.get_text(strip=True) or 
                           f"数据中心_{len(results)+1}")
                    
                    if 30.6 <= lat <= 31.9 and 120.8 <= lng <= 122.2:
                        results.append({
                            'name': name,
                            'latitude': lat,
                            'longitude': lng,
                            'location': '上海市',
                            'source_page': self.extract_page_number(source),
                            'extraction_method': 'HTML_DOM',
                            'source': source,
                            'raw_data': {
                                'name': name,
                                'latitude': lat,
                                'longitude': lng
                            }
                        })
                except (ValueError, TypeError):
                    continue
        except:
            pass
        
        return results
    
    def process_json_response(self, data, source):
        """处理JSON响应数据"""
        results = []
        
        try:
            if isinstance(data, dict):
                # 如果是字典，查找数据数组
                for key, value in data.items():
                    if isinstance(value, list) and value:
                        results.extend(self.process_json_array(value, source))
            elif isinstance(data, list):
                # 如果是数组，直接处理
                results.extend(self.process_json_array(data, source))
        except:
            pass
        
        return results
    
    def process_json_array(self, data_array, source):
        """处理JSON数组数据"""
        results = []
        
        for item in data_array:
            if not isinstance(item, dict):
                continue
            
            # 尝试提取坐标信息
            lat = item.get('latitude') or item.get('lat') or item.get('y')
            lng = item.get('longitude') or item.get('lng') or item.get('x')
            
            if lat is not None and lng is not None:
                try:
                    lat, lng = float(lat), float(lng)
                    
                    # 验证坐标范围
                    if 30.6 <= lat <= 31.9 and 120.8 <= lng <= 122.2:
                        name = (item.get('name') or 
                               item.get('title') or 
                               item.get('label') or 
                               f"数据中心_{len(results)+1}")
                        
                        results.append({
                            'name': name,
                            'latitude': lat,
                            'longitude': lng,
                            'location': '上海市',
                            'source_page': self.extract_page_number(source),
                            'extraction_method': 'JSON',
                            'source': source,
                            'raw_data': item
                        })
                except ValueError:
                    continue
        
        return results
    
    def extract_page_number(self, source):
        """从源标识中提取页码"""
        page_patterns = [
            r'page_?(\d+)',
            r'p(\d+)',
            r'offset_?(\d+)',
        ]
        
        for pattern in page_patterns:
            match = re.search(pattern, str(source), re.IGNORECASE)
            if match:
                try:
                    if 'offset' in pattern:
                        # 偏移量转页码 (假设每页40个)
                        return int(match.group(1)) // 40 + 1
                    else:
                        return int(match.group(1))
                except:
                    pass
        
        return 1  # 默认第1页
    
    def run_smart_crawl(self):
        """运行智能翻页爬虫"""
        print("🚀 上海数据中心智能翻页爬虫启动")
        print("🎯 目标：通过多种方法获取所有54个数据中心")
        print("="*70)
        
        # 1. 分析页面结构
        analysis = self.analyze_page_structure()
        if not analysis:
            print("❌ 页面分析失败")
            return []
        
        # 2. 尝试不同的翻页方法
        all_results, methods = self.try_different_pagination_approaches()
        
        # 3. 去重处理
        unique_results = self.deduplicate_results(all_results)
        
        # 4. 按页面分组
        self.group_by_pages(unique_results)
        
        print(f"\n{'='*70}")
        print(f"📊 智能爬取结果:")
        print(f"  成功方法: {methods}")
        print(f"  原始数据: {len(all_results)} 个")
        print(f"  去重后数据: {len(unique_results)} 个")
        print(f"  目标完成度: {len(unique_results)}/54 ({len(unique_results)/54*100:.1f}%)")
        
        # 按页统计
        page_stats = {}
        for result in unique_results:
            page = result['source_page']
            page_stats[page] = page_stats.get(page, 0) + 1
        
        print(f"\n按页面统计:")
        for page in sorted(page_stats.keys()):
            print(f"  第 {page} 页: {page_stats[page]} 个数据中心")
        
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
                unique_results.append(result)
        
        print(f"{len(unique_results)}")
        return unique_results
    
    def group_by_pages(self, results):
        """按页面分组"""
        for result in results:
            page_key = f"page_{result['source_page']}"
            if page_key not in self.page_data:
                self.page_data[page_key] = []
            self.page_data[page_key].append(result)
    
    def save_results(self, results):
        """保存结果"""
        if not results:
            print("❌ 没有数据需要保存")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存JSON数据
        json_file = f"data/shanghai/上海数据中心智能翻页_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON文件已保存: {json_file}")
        
        # 保存分页数据
        page_file = f"data/shanghai/分页数据_{timestamp}.json"
        with open(page_file, 'w', encoding='utf-8') as f:
            json.dump(self.page_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 分页数据已保存: {page_file}")
        
        # 生成报告
        self.generate_smart_report(results, timestamp)
    
    def generate_smart_report(self, results, timestamp):
        """生成智能爬取报告"""
        report_file = f"data/shanghai/智能翻页报告_{timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("上海数据中心智能翻页爬取报告\n")
            f.write("="*60 + "\n\n")
            
            f.write(f"爬取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总数据中心: {len(results)} 个\n")
            f.write(f"目标完成度: {len(results)}/54 ({len(results)/54*100:.1f}%)\n\n")
            
            # 按提取方法统计
            method_stats = {}
            for result in results:
                method = result.get('extraction_method', '未知')
                method_stats[method] = method_stats.get(method, 0) + 1
            
            f.write("提取方法统计:\n")
            f.write("-"*30 + "\n")
            for method, count in method_stats.items():
                f.write(f"{method}: {count} 个\n")
            f.write("\n")
            
            # 按页面统计
            page_stats = {}
            for result in results:
                page = result['source_page']
                page_stats[page] = page_stats.get(page, 0) + 1
            
            f.write("页面统计:\n")
            f.write("-"*30 + "\n")
            for page in sorted(page_stats.keys()):
                f.write(f"第 {page} 页: {page_stats[page]} 个数据中心\n")
            f.write("\n")
            
            # 详细数据列表
            f.write("数据中心详细列表:\n")
            f.write("-"*30 + "\n")
            for i, dc in enumerate(results, 1):
                f.write(f"{i:2d}. {dc['name']}\n")
                f.write(f"    坐标: ({dc['latitude']:.6f}, {dc['longitude']:.6f})\n")
                f.write(f"    来源页: 第{dc['source_page']}页\n")
                f.write(f"    提取方法: {dc['extraction_method']}\n")
                f.write(f"    数据源: {dc['source']}\n\n")
        
        print(f"✅ 智能报告已保存: {report_file}")

def main():
    """主函数"""
    print("🎯 上海数据中心智能翻页爬虫")
    print("🔄 不依赖WebDriver的JavaScript翻页处理")
    print("📄 目标：第1页40个，第2页14个，共54个数据中心")
    
    crawler = SmartPaginationCrawler()
    
    try:
        # 运行智能爬虫
        results = crawler.run_smart_crawl()
        
        if results:
            print(f"\n🎉 智能爬取完成！")
            print(f"✅ 获取到 {len(results)} 个上海数据中心")
            
            # 显示前10个结果预览
            print(f"\n📋 前10个数据中心预览:")
            for i, dc in enumerate(results[:10], 1):
                print(f"  {i:2d}. {dc['name']} (第{dc['source_page']}页, {dc['extraction_method']})")
            
            if len(results) > 10:
                print(f"     ... 还有 {len(results) - 10} 个")
            
            # 保存结果
            crawler.save_results(results)
            
            # 检查目标达成情况
            if len(results) >= 54:
                print(f"\n🎯 目标达成！获取到 {len(results)} 个数据中心 (目标54个)")
            else:
                print(f"\n⚠️ 距离目标还差 {54 - len(results)} 个数据中心")
                print(f"建议：可能需要进一步分析网站的JavaScript翻页机制")
            
        else:
            print("❌ 未获取到任何数据")
            
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断爬取")
    except Exception as e:
        print(f"❌ 爬取过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
