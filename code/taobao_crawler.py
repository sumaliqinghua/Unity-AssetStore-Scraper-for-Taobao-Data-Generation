from base_crawler import BaseCrawler
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
import time
import requests
import json

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
            description = self.extract_description_text(html_content)
            if not description:
                return None
                
            return {
                'title': custom_title or "未命名",
                'url': url,
                'content': description,
                'translated_content': self.translate_text(description),
                'file_path': file_path
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
                    self.logger.warning(f"解析JSON-LD时出错: {e}")
            
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

    def download_image(self, html_content, save_dir='images'):
        """
        从HTML内容中下载图片，最多下载5张
        Args:
            html_content: HTML内容
            save_dir: 保存目录
        Returns:
            list: 下载的图片路径列表
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            downloaded_images = []
            
            # 确保保存目录存在
            os.makedirs(save_dir, exist_ok=True)
            
            # 查找所有带background-image样式的元素
            elements_with_bg = soup.find_all(lambda tag: tag.get('style') and 'background-image' in tag.get('style'))
            
            # 查找所有img标签
            img_tags = soup.find_all('img')
            
            # 提取所有图片URL
            image_urls = []
            
            # 从background-image中提取URL
            for element in elements_with_bg:
                style = element.get('style', '')
                if 'url(' in style:
                    url = style.split('url(')[1].split(')')[0].strip('"\'&quot;')
                    if url:
                        image_urls.append(url)
            
            # 从img标签中提取URL
            for img in img_tags:
                url = img.get('src')
                if url:
                    image_urls.append(url)
            
            # 限制最多下载5张图片
            for i, url in enumerate(image_urls[:5]):
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
                    file_name = f'image_{i+1}{file_ext}'
                    save_path = os.path.join(save_dir, file_name)
                    
                    # 下载图片
                    response = self.session.get(url, stream=True)
                    if response.status_code == 200:
                        with open(save_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                        downloaded_images.append(save_path)
                        self.logger.info(f'成功下载图片: {save_path}')
                    else:
                        self.logger.warning(f'下载图片失败: {url}')
                except Exception as e:
                    self.logger.error(f'下载图片出错: {url} - {str(e)}')
                    continue
                
                # 添加延迟
                time.sleep(self.delay)
            
            return downloaded_images
            
        except Exception as e:
            self.logger.error(f'下载图片时出错: {e}')
            return []

# 使用示例
if __name__ == "__main__":
    crawler = TaoBaoCrawler()
    urls = [
        "https://assetstore.unity.com/packages/2d/environments/2d-rpg-topdown-tilesets-pixelart-assets-full-bundle-212921?srsltid=AfmBOoq8TNtGTyNgIzhkw30EOjhIn2ABvKE7WQ2XNX4TtgP-x_B22C6t",
    ]
    
    # 开始爬取
    results = crawler.crawl_urls(urls)
    print(f"成功爬取 {len(results)} 个页面")
    # 从文件读取HTML内容
    # with open('code/a.html', 'r', encoding='utf-8') as f:
    #     html_content = f.read()
    
    # # 提取文本
    # result = crawler.extract_description_text(html_content)
    print(results)
