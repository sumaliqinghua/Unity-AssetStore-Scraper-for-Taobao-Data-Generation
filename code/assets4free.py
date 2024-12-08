import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
import time
from concurrent.futures import ThreadPoolExecutor
import logging
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin
import json

class WebsiteScraper:
    def __init__(self, base_url, max_workers=3, delay=1):
        self.base_url = base_url
        self.max_workers = max_workers
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
      
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
      
        # 创建下载目录
        self.download_dir = 'downloads'
        os.makedirs(self.download_dir, exist_ok=True)
      
        # 检查robots.txt
        self.robots = RobotFileParser()
        self.robots.set_url(urljoin(base_url, '/robots.txt'))
        try:
            self.robots.read()
        except Exception as e:
            self.logger.warning(f"无法读取robots.txt: {e}")

    def can_fetch(self, url):
        try:
            return self.robots.can_fetch("*", url)
        except Exception:
            return True

    def download_image(self, img_url, title):
        if not img_url:
            return None
          
        try:
            # 创建安全的文件名
            safe_title = "".join(x for x in title if x.isalnum() or x in (' ', '-', '_')).rstrip()
            ext = os.path.splitext(urllib.parse.urlparse(img_url).path)[1]
            img_filename = os.path.join(self.download_dir, f"{safe_title}{ext}")
          
            # 检查文件是否已存在
            if os.path.exists(img_filename):
                self.logger.info(f"图片已存在: {img_filename}")
                return img_filename
              
            response = self.session.get(img_url, timeout=10)
            response.raise_for_status()
          
            with open(img_filename, 'wb') as f:
                f.write(response.content)
          
            self.logger.info(f"已下载图片: {img_filename}")
            return img_filename
          
        except Exception as e:
            self.logger.error(f"下载图片失败 {img_url}: {e}")
            return None

    def parse_article(self, html_content, url):
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            article = soup.find('article')
          
            if not article:
                return None
              
            # 提取数据
            title = article.find('h2', class_='single-post-title')
            title = title.text.strip() if title else "无标题"
          
            thumbnail = article.find('div', class_='thumbnail')
            img_url = thumbnail.find('img')['src'] if thumbnail else None
          
            content = article.find('div', class_='entry-content')
            content_text = '\n'.join([p.text.strip() for p in content.find_all('p')]) if content else ''
          
            return {
                'title': title,
                'image_url': img_url,
                'content': content_text,
                'url': url
            }
          
        except Exception as e:
            self.logger.error(f"解析文章失败 {url}: {e}")
            return None

    def save_article(self, article_data):
        if not article_data:
            return False
          
        try:
            # 下载图片
            img_filename = self.download_image(article_data['image_url'], article_data['title'])
          
            # 保存文章内容
            safe_title = "".join(x for x in article_data['title'] if x.isalnum() or x in (' ', '-', '_')).rstrip()
            content_filename = os.path.join(self.download_dir, f"{safe_title}.txt")
          
            with open(content_filename, 'w', encoding='utf-8') as f:
                f.write(f"标题: {article_data['title']}\n")
                f.write(f"URL: {article_data['url']}\n")
                f.write(f"图片: {article_data['image_url']}\n\n")
                f.write("正文内容:\n")
                f.write(article_data['content'])
          
            # 保存元数据
            metadata_filename = os.path.join(self.download_dir, f"{safe_title}.json")
            with open(metadata_filename, 'w', encoding='utf-8') as f:
                json.dump(article_data, f, ensure_ascii=False, indent=2)
          
            return True
          
        except Exception as e:
            self.logger.error(f"保存文章失败 {article_data['title']}: {e}")
            return False

    def process_url(self, url):
        if not self.can_fetch(url):
            self.logger.warning(f"robots.txt 禁止访问: {url}")
            return None
          
        try:
            time.sleep(self.delay)  # 请求延迟
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
          
            article_data = self.parse_article(response.text, url)
            if article_data:
                if self.save_article(article_data):
                    self.logger.info(f"成功处理文章: {article_data['title']}")
                    return article_data
                  
        except Exception as e:
            self.logger.error(f"处理URL失败 {url}: {e}")
      
        return None

    def scrape_urls(self, urls):
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(self.process_url, url): url for url in urls}
            for future in future_to_url:
                result = future.result()
                if result:
                    results.append(result)
        return results

# 使用示例
if __name__ == "__main__":
    base_url = "https://unityassets4free.com/"  # 替换为目标网站
    urls = [
        "https://unityassets4free.com/tile-world-match/",  # 替换为实际的URL列表
        "https://unityassets4free.com/arcade-ultimate-vehicles-pack-low-poly-cars/",
        # ... 更多URL
    ]
  
    scraper = WebsiteScraper(base_url, max_workers=3, delay=1)
    results = scraper.scrape_urls(urls)
  
    print(f"成功处理 {len(results)} 个页面")
  
    # 保存总结报告
    with open(os.path.join(scraper.download_dir, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)