from base_crawler import BaseCrawler
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
import time
import requests
import json
import re

class TaoBaoCrawler(BaseCrawler):
    def __init__(self, max_workers=3, delay=1):
        super().__init__(
            base_url="https://assetstore.unity.com",  # 修正基础URL
            max_workers=max_workers,
            delay=delay,
            use_proxy=False,  # 禁用代理
            disable_ssl_verification=True  # 禁用SSL验证
        )

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
            
            # 获取描述
            description = None
            meta_desc = soup.find('meta', property='og:description')
            if meta_desc:
                description = meta_desc.get('content')
            if not description:
                meta_desc = soup.find('meta', {'name': 'description'})
                if meta_desc:
                    description = meta_desc.get('content')
            
            if not description:
                description = self.extract_description_text(html_content)
                
            if not description:
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
                    self.logger.warning(f"解析JSON-LD数据时出错: {str(e)}")
            
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
                        self.logger.debug(f"解析脚本中的图片数组时出错: {str(e)}")
            
            # 5. 处理找到的所有图片URL
            for img_url in image_urls:
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
            
            return {
                'title': title,
                'url': url,
                'content': description,
                'translated_content': self.translate_text(description),
                'file_path': file_path,
                'file_name': file_name,
                'image_paths': images
            }
            
        except Exception as e:
            self.logger.error(f"解析文章失败: {e}")
            return None

    def extract_description_text(self, html_content):
        """
        Extract text from description divs based on their structure
        
        Args:
            html_content: HTML content as string
        Returns:
            str: Concatenated text from the divs with proper formatting
        """
        try:
            if not html_content:
                self.logger.error("HTML内容为空")
                return ""
                
            self.logger.info(f"HTML内容长度: {len(html_content)}")
            soup = BeautifulSoup(html_content, 'html.parser')
            texts = []
            
            # 打印页面标题，帮助确认页面是否正确加载
            title = soup.find('title')
            if title:
                self.logger.info(f"页面标题: {title.text}")
                texts.append(f"标题: {title.text}")
            
            # 尝试从meta description获取描述
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                self.logger.info("找到meta description")
                texts.append(f"描述: {meta_desc['content']}")
            
            # 尝试从JSON-LD中获取描述
            script_tags = soup.find_all('script', {'type': 'application/ld+json'})
            for script in script_tags:
                try:
                    json_data = json.loads(script.string)
                    if isinstance(json_data, dict):
                        if 'description' in json_data:
                            self.logger.info("从JSON-LD中找到描述")
                            texts.append(f"详细描述: {json_data['description']}")
                except Exception as e:
                    self.logger.warning(f"解析JSON-LD数据时出错: {e}")
            
            # 查找所有可能包含描述的div
            description_divs = soup.find_all(['div', 'p'], class_=lambda x: x and any(keyword in str(x).lower() for keyword in ['description', 'content', 'detail', 'info']))
            for div in description_divs:
                text = ' '.join(line.strip() for line in div.get_text().splitlines() if line.strip())
                if text and len(text) > 50:  # 只保留较长的文本，避免无用信息
                    self.logger.info(f"找到描述div: {text[:100]}...")
                    texts.append(text)
            
            if not texts:
                # 保存HTML内容以供调试
                debug_file = 'debug_html.txt'
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                self.logger.warning(f"未找到任何描述内容，已保存HTML到{debug_file}")
                return ""
                
            return '\n\n'.join(texts)
            
        except Exception as e:
            self.logger.error(f"提取描述文本时出错: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return ""

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
        try:
            # 确保保存目录存在
            os.makedirs(save_dir, exist_ok=True)
            
            # 处理URL
            url = url.strip()
            if not url.startswith(('http://', 'https://')):
                if url.startswith('//'):
                    url = 'https:' + url
                else:
                    url = urljoin(self.base_url, url)
        
            try:
                # 生成文件名
                file_ext = os.path.splitext(url.split('?')[0])[1] or '.jpg'
                file_name = f'image_{int(time.time())}_{hash(url) % 10000}{file_ext}'
                save_path = os.path.join(save_dir, file_name)
            
                # 下载图片
                response = self.session.get(url, stream=True)
                if response.status_code == 200:
                    with open(save_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    self.logger.info(f'成功下载图片: {save_path}')
                    return save_path
                else:
                    self.logger.warning(f'下载图片失败: {url}')
                    return None
                    
            except Exception as e:
                self.logger.error(f'下载图片出错: {url} - {str(e)}')
                return None
        
        except Exception as e:
            self.logger.error(f'下载图片时出错: {e}')
            return None

# 使用示例
if __name__ == "__main__":
    # 示例URLs
    urls = [
        "https://assetstore.unity.com/packages/3d/environments/landscapes/terrain-sample-asset-pack-145808",
    ]
    
    # 创建爬虫实例 - 禁用代理和SSL验证
    crawler = TaoBaoCrawler(max_workers=3, delay=1)
    crawler.session.proxies = {}  # 禁用代理
    crawler.session.verify = False  # 禁用SSL验证
    
    # 开始爬取
    results = crawler.crawl_urls(urls)
    
    # 测试图片下载
    if results and len(results) > 0:
        # 获取第一个结果的HTML内容
        html_content = crawler.get_page_content(results[0]['url'])
        # 重新解析以测试图片下载
        article_with_images = crawler.parse_article(html_content, results[0]['url'], results[0]['title'])
        if article_with_images and 'image_paths' in article_with_images:
            print(f"\n下载的图片路径:")
            for img_path in article_with_images['image_paths']:
                print(f"- {img_path}")
    
    print(f"成功爬取 {len(results)} 个页面")
    print(results)
