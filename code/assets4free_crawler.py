from base_crawler import BaseCrawler
from bs4 import BeautifulSoup
import os
import re
from urllib.parse import urljoin
import time

class Assets4FreeCrawler(BaseCrawler):
    def __init__(self, max_workers=3, delay=1):
        super().__init__(
            base_url="https://unityassets4free.com",
            max_workers=max_workers,
            delay=delay
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
                # 尝试从文章内容中提取描述
                article = soup.find('article')
                if article:
                    description = article.get_text(strip=True)
                
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
            
            # 查找所有可能的图片容器
            image_containers = soup.find_all(['div', 'figure'], class_=lambda x: x and any(keyword in str(x).lower() for keyword in ['gallery', 'slider', 'image', 'featured']))
            
            # 从容器中提取图片URL
            image_urls = set()
            for container in image_containers:
                # 查找所有图片标签
                img_tags = container.find_all('img', src=True)
                for img in img_tags:
                    img_url = img.get('src')
                    if img_url:
                        # 转换为绝对URL
                        if not img_url.startswith(('http://', 'https://')):
                            img_url = urljoin(url, img_url)
                        image_urls.add(img_url)
                
                # 查找所有data-src属性
                img_tags = container.find_all(attrs={'data-src': True})
                for img in img_tags:
                    img_url = img.get('data-src')
                    if img_url:
                        if not img_url.startswith(('http://', 'https://')):
                            img_url = urljoin(url, img_url)
                        image_urls.add(img_url)
            
            # 限制最多7张图片
            downloaded_count = 0
            for img_url in image_urls:
                if downloaded_count >= 7:
                    break
                
                # 确保获取最大尺寸的图片
                img_url = img_url.replace('-150x150', '')\
                               .replace('-300x300', '')\
                               .replace('-768x768', '')\
                               .replace('-1024x1024', '')\
                               .replace('-thumbnail', '')
                
                self.logger.info(f'尝试下载图片: {img_url}')
                img_path = self.download_image(img_url, save_dir)
                if img_path:
                    images.append(img_path)
                    self.logger.info(f'成功下载图片: {img_path}')
                    downloaded_count += 1
            
            # 翻译描述文本
            translated_description = self.translate_text(description) if description else ""
            
            return {
                'title': title,
                'url': selected_result['link'] if 'selected_result' in locals() else url,  # 使用搜索结果的链接
                'content': description,
                'translated_content': translated_description,
                'file_path': file_path,
                'file_name': file_name,
                'save_dir': os.path.abspath(save_dir),  # 使用绝对路径
                'image_paths': images
            }
            
        except Exception as e:
            self.logger.error(f"解析页面时出错: {e}")
            return None

    def crawl_single_url(self, url):
        """针对assets4free的单个URL爬取实现"""
        try:
            html_content = self.get_page_content(url)
            return self.parse_article(html_content, url)
        except Exception as e:
            self.logger.error(f"爬取URL失败 {url}: {e}")
            return None

    def crawl_urls(self, urls):
        """爬取多个URL"""
        return super().crawl_urls(urls)

# 使用示例
if __name__ == "__main__":
    # 示例URLs
    urls = [
        "https://unityassets4free.com/cute-town-3d/",
        "https://unityassets4free.com/arcade-racing-game-template/",
    ]
    
    # 创建爬虫实例
    crawler = Assets4FreeCrawler(max_workers=3, delay=1)
    
    # 开始爬取
    results = crawler.crawl_urls(urls)
    print(f"成功爬取 {len(results)} 个页面")
