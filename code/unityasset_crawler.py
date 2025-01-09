from base_crawler import BaseCrawler
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
import time
import requests
import json
import re
import pandas as pd
from datetime import datetime

class UnityAssetCrawler(BaseCrawler):
    def __init__(self, max_workers=3, delay=1):
        super().__init__(
            base_url="https://assetstore.unity.com",  # 修正基础URL
            max_workers=max_workers,
            delay=delay,
            use_proxy=False,  # 禁用代理
            disable_ssl_verification=True  # 禁用SSL验证
        )
        # 显式禁用所有代理设置
        self.session.proxies.clear()
        self.session.trust_env = False  # 禁用环境变量中的代理设置
        self.session.verify = False  # 显式禁用SSL验证

    def parse_article(self, html_content, url, custom_title=None, file_path=None):
        """
        解析页面内容
        Args:
            html_content: HTML内容
            url: 页面URL
            custom_title: 自定义标题（可选）
            file_path: 文件路径（可选）
        Returns:
            dict: 包含解析后的内容
        """
        try:
            # 保存HTML内容到文件
            debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'debug')
            os.makedirs(debug_dir, exist_ok=True)
            debug_file = os.path.join(debug_dir, f'page_{int(time.time())}.html')
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(f"<!-- Original URL: {url} -->\n")
                f.write(html_content)
            self.logger.info(f"已保存HTML内容到: {debug_file}")

            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 获取标题
            title = custom_title
            if not title:
                meta_title = soup.find('meta', property='og:title')
                if meta_title:
                    title = meta_title.get('content', '未命名')
                else:
                    title_tag = soup.find('title')
                    title = title_tag.text if title_tag else '未命名'
            
            # 获取文本
            content = None
            
            if not content:
                content = self.extract_content_text(html_content)
                
            if not content:
                return None
            
            # 生成文件名 - 移除所有非法字符
            file_name = title.replace(' ', '_')
            # 移除Windows文件名中的非法字符 \ / : * ? " < > |
            file_name = re.sub(r'[\\/:*?"<>|]', '_', file_name)
            # 确保文件名不超过255个字符
            if len(file_name) > 255:
                file_name = file_name[:255]
            
            # 创建文章目录
            save_dir = self.create_article_directory(file_name)
            
            # 提取并下载图片
            images = []
            
            # 2. 查找轮播图片
            # Unity Asset Store的图片通常存储在特定的CDN上
            cdn_pattern = re.compile(r'(?:https?:)?//assetstorev1-prd-cdn\.unity3d\.com/.*?\.(jpg|png|jpeg|gif)(\?v=\d+)?')
            
            # 1. 从页面数据中查找图片URL
            image_urls = set()  # 使用set去重
            
            # 2. 从JSON-LD数据中提取图片
            json_ld_pattern = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.DOTALL)
            json_matches = json_ld_pattern.findall(html_content)
            
            for json_str in json_matches:
                try:
                    data = json.loads(json_str)
                    if isinstance(data, dict):
                        # 检查image字段
                        if 'image' in data:
                            if isinstance(data['image'], list):
                                for img in data['image']:
                                    if isinstance(img, str):
                                        img_url = img if img.startswith('http') else f'https:{img}'
                                        if cdn_pattern.search(img_url):
                                            image_urls.add(img_url)
                            elif isinstance(data['image'], str):
                                img_url = data['image'] if data['image'].startswith('http') else f'https:{data["image"]}'
                                if cdn_pattern.search(img_url):
                                    image_urls.add(img_url)
                except Exception as e:
                    self.logger.warning(f"解析JSON-LD数据时出错: {e}")
            
            # 3. 从meta标签中提取图片
            meta_images = soup.find_all('meta', {'property': ['og:image', 'twitter:image']})
            for meta in meta_images:
                img_url = meta.get('content')
                if img_url:
                    img_url = img_url if img_url.startswith('http') else f'https:{img_url}'
                    if cdn_pattern.search(img_url):
                        image_urls.add(img_url)
            
            # 4. 查找所有script标签中的图片URL
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # 查找所有可能的图片URL
                    matches = cdn_pattern.findall(script.string)
                    for match in matches:
                        img_url = match[0]  # 完整的URL在第一个分组
                        img_url = img_url if img_url.startswith('http') else f'https:{img_url}'
                        image_urls.add(img_url)
                    
                    # 尝试解析JavaScript对象
                    try:
                        # 查找类似 "images": ["url1", "url2"] 的模式
                        img_arrays = re.findall(r'"(?:images|screenshots|gallery)":\s*\[(.*?)\]', script.string)
                        for img_array in img_arrays:
                            # 提取数组中的URL
                            url_matches = re.findall(r'"((?:https?:)?//[^"]+\.(?:jpg|png|jpeg|gif)[^"]*)"', img_array)
                            for url in url_matches:
                                img_url = url if url.startswith('http') else f'https:{url}'
                                if cdn_pattern.search(img_url):
                                    image_urls.add(img_url)
                    except Exception as e:
                        self.logger.debug(f"解析脚本中的图片数组时出错: {e}")
            
            # 5. 处理找到的所有图片URL（限制最多7张）
            downloaded_count = 0
            for img_url in image_urls:
                if downloaded_count >= 7:
                    break
                    
                # 确保获取最大尺寸的图片
                img_url = img_url.replace('_50x50.jpg', '.jpg')\
                               .replace('_60x60.jpg', '.jpg')\
                               .replace('_100x100.jpg', '.jpg')\
                               .replace('_thumb.jpg', '.jpg')\
                               .replace('_preview.jpg', '.jpg')
                
                self.logger.info(f'尝试下载图片: {img_url}')
                img_path = self.download_image(img_url, save_dir)
                if img_path:
                    images.append(img_path)
                    self.logger.info(f'成功下载图片: {img_path}')
                    downloaded_count += 1
            
            # 翻译描述文本
            translated_content = self.translate_text(content) if content else ""
            
            return {
                'title': title,
                'url': url,  # 使用传入的URL
                'content': content,
                'translated_content': translated_content,
                'file_path': file_path,
                'file_name': file_name,
                'save_dir': os.path.abspath(save_dir),  # 使用绝对路径
                'image_paths': images
            }
            
        except Exception as e:
            self.logger.error(f"解析页面时出错: {e}")
            return None

    def extract_content_text(self, html_content):

        return html_content
    

    def crawl_single_url(self, url):
        """针对单个URL爬取实现"""
        try:
            self.logger.info(f"开始爬取URL: {url}")
            html_content = self.get_page_content(url)
            if html_content is None:
                self.logger.error("获取页面内容失败")
                return None
                
            self.logger.info("成功获取页面内容，开始解析...")
            result = self.parse_article(html_content, url)
            if result:
                self.logger.info("成功解析文章内容")
            else:
                self.logger.warning("解析文章内容为空")
            return result
        except Exception as e:
            self.logger.error(f"爬取URL失败 {url}: {e}")
            return None

    def get_page_content(self, url, timeout=30):
        """获取页面内容"""
        try:
            # 创建一个新的session，确保没有代理设置
            direct_session = requests.Session()
            direct_session.headers = self.session.headers
            direct_session.verify = self.session.verify
            direct_session.proxies = {}  # 显式禁用代理
            
            response = direct_session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.logger.error(f"获取页面内容失败: {e}")
            return None

    def download_image(self, url, save_dir='images'):
        """
        下载单个图片
        Args:
            url: 图片URL
            save_dir: 保存目录
        Returns:
            str: 下载的图片路径，如果失败则返回None
        """
        max_retries = 5
        timeout = 60
        
        try:
            # 确保保存目录存在
            os.makedirs(save_dir, exist_ok=True)
            
            # 处理URL
            url = url.strip()
            if not url.startswith(('http://', 'https://')):
                if url.startswith('//'):
                    url = 'https:' + url
                elif url.startswith('/'):
                    url = urljoin(self.base_url, url)
                else:
                    url = urljoin(self.base_url, '/' + url)

            # 创建专用的下载session
            download_session = requests.Session()
            download_session.verify = False  # 禁用SSL验证
            download_session.trust_env = False  # 禁用环境变量代理
            download_session.proxies = {}  # 显式禁用代理
            
            # 设置headers模拟浏览器
            download_session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': self.base_url,
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'image',
                'sec-fetch-mode': 'no-cors',
                'sec-fetch-site': 'cross-site'
            })

            for attempt in range(max_retries):
                try:
                    # 生成文件名
                    file_ext = os.path.splitext(url.split('?')[0])[1]
                    if not file_ext or file_ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                        file_ext = '.jpg'
                    file_name = f'image_{int(time.time())}_{hash(url) % 10000}{file_ext}'
                    save_path = os.path.join(save_dir, file_name)
                
                    # 下载图片
                    response = download_session.get(url, stream=True, timeout=timeout)
                    response.raise_for_status()
                    
                    # 检查内容类型
                    content_type = response.headers.get('content-type', '')
                    if not content_type.startswith('image/'):
                        self.logger.warning(f'非图片内容类型: {content_type}, URL: {url}')
                        continue

                    # 保存图片
                    with open(save_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    # 验证文件大小
                    if os.path.getsize(save_path) < 100:  # 小于100字节可能是无效图片
                        os.remove(save_path)
                        raise Exception("Downloaded file too small")
                        
                    self.logger.info(f'成功下载图片: {save_path}')
                    return save_path
                    
                except requests.exceptions.RequestException as e:
                    self.logger.warning(f'下载图片失败 (尝试 {attempt + 1}/{max_retries}): {url} - {str(e)}')
                    if attempt == max_retries - 1:
                        return None
                    time.sleep(1)  # 重试前等待
                except Exception as e:
                    self.logger.error(f'下载图片出错: {url} - {str(e)}')
                    if attempt == max_retries - 1:
                        return None
                    time.sleep(1)  # 重试前等待
        
        except Exception as e:
            self.logger.error(f'下载图片时出错: {e}')
            return None

    def save_to_excel(self):
        """
        重写基类的save_to_excel方法，处理空描述和翻译描述的情况
        """
        excel_file = os.path.join(self.base_download_dir, 'assets_data.xlsx')

        # 转换数据为DataFrame
        df_data = []
        for result in self.results:
            # 确保save_dir使用绝对路径
            save_dir = result.get('save_dir', '')
            if save_dir and not os.path.isabs(save_dir):
                save_dir = os.path.abspath(save_dir)

            # 处理空描述和翻译描述
            content = result.get('content', '')
            translated_content = result.get('translated_content', '')

            row = {
                '标题': result.get('title', ''),
                '链接': result.get('url', ''),
                '描述': '',
                '翻译后的描述': '',
                '文件路径': result.get('file_path', ''),
                '文件名': result.get('file_name', ''),
                '图片文件夹': save_dir
            }
            df_data.append(row)

        # 创建DataFrame并保存到Excel
        df = pd.DataFrame(df_data)
        df.to_excel(excel_file, index=False, engine='openpyxl')
        self.logger.info(f"数据已保存到Excel文件: {excel_file}")
    def translate_text(self, text):
        return ''
    def crawl_urls(self, urls):
        """爬取多个URL"""
        return super().crawl_urls(urls)

# 使用示例
if __name__ == "__main__":
    # 示例URLs
    urls = [
        "https://assetstore.unity.com/packages/3d/environments/landscapes/terrain-sample-asset-pack-145808",
    ]
    
    # 创建爬虫实例
    crawler = UnityAssetCrawler(max_workers=3, delay=1)
    
    try:
        # 获取页面内容
        response = crawler.session.get(urls[0])
        response.raise_for_status()
                            
        # 解析页面内容
        parsed_content = crawler.parse_article(response.text, urls[0])
        
        if parsed_content:
            print("\n成功解析页面内容")
            if 'image_paths' in parsed_content:
                print(f"\n下载的图片路径:")
                for img_path in parsed_content['image_paths']:
                    print(f"- {img_path}")
            else:
                print("未找到图片")
        else:
            print("页面解析失败")
            
    except Exception as e:
        print(f"爬取过程中出错: {str(e)}")
