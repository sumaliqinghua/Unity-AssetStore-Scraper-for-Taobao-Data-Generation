from base_crawler import BaseCrawler
from bs4 import BeautifulSoup

class Assets4FreeCrawler(BaseCrawler):
    def __init__(self, max_workers=3, delay=1):
        super().__init__(
            base_url="https://unityassets4free.com/",
            max_workers=max_workers,
            delay=delay,
            use_proxy=True  # 特定于assets4free的配置
    )

    def parse_article(self, html_content, url, custom_title=None, file_path=None):
        """针对assets4free网站的具体解析实现"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            article = soup.find('article')
            
            if not article:
                return None
                
            # 使用提供的标题或从文章中提取
            title = custom_title if custom_title else article.find('h2', class_='single-post-title').text.strip() if article.find('h2', class_='single-post-title') else "无标题"
            
            thumbnail = article.find('div', class_='thumbnail')
            img_url = thumbnail.find('img')['src'] if thumbnail else None
            
            content = article.find('div', class_='entry-content')
            content_text = '\n'.join([p.text.strip() for p in content.find_all('p')]) if content else ''
            
            # 翻译内容
            translated_content = self.translate_text(content_text)
            
            # 生成处理后的文件名
            file_name = title.replace(' ', '_').replace(':', '_')
            
            # 创建文章目录
            save_dir = self.create_article_directory(file_name)
            
            # 下载缩略图
            image_path = self.download_image(img_url, save_dir) if img_url else None
            
            # 准备数据
            article_data = {
                'title': title,
                'url': url,
                'content': content_text,
                'translated_content': translated_content,
                'file_path': file_path,
                'file_name': file_name,
                'image_path': image_path
            }
            
            # 保存到Excel
            self.save_to_excel(article_data)
            
            return article_data
            
        except Exception as e:
            self.logger.error(f"解析文章失败 {url}: {e}")
            return None

    def crawl_single_url(self, url):
        """针对assets4free的单个URL爬取实现"""
        try:
            html_content = self.get_page_content(url)
            return self.parse_article(html_content, url)
        except Exception as e:
            self.logger.error(f"爬取URL失败 {url}: {e}")
            return None

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
