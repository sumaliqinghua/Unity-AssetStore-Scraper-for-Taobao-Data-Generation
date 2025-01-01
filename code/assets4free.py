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
from hashlib import md5
from translate import Translator
import pandas as pd

class WebsiteScraper:
    def __init__(self, base_url, max_workers=3, delay=1, disable_ssl_verification=False):
        self.base_url = base_url
        self.max_workers = max_workers
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # 配置代理
        self.session.proxies = {
            "http": "http://127.0.0.1:2612",
            "https": "http://127.0.0.1:2612",
        }
        
        # 配置SSL验证
        self.session.verify = not disable_ssl_verification
        
        # 初始化翻译器
        self.translator = Translator(to_lang="zh")
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scraper.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 创建基础下载目录
        self.base_download_dir = 'downloads'
        os.makedirs(self.base_download_dir, exist_ok=True)
        
        # 检查robots.txt
        self.robots = RobotFileParser()
        self.robots.set_url(urljoin(base_url, '/robots.txt'))
        try:
            self.robots.read()
        except Exception as e:
            self.logger.warning(f"无法读取robots.txt: {e}")

    def translate_text(self, text):
        """翻译文本，包含错误处理和重试机制"""
        if not text:
            return ""
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 将文本分成较小的块进行翻译
                chunks = [text[i:i+500] for i in range(0, len(text), 500)]
                translated_chunks = []
                
                for chunk in chunks:
                    translated = self.translator.translate(chunk)
                    translated_chunks.append(translated)
                    time.sleep(0.5)  # 避免翻译服务限制
                
                return " ".join(translated_chunks)
            
            except Exception as e:
                if attempt == max_retries - 1:
                    self.logger.error(f"翻译失败: {e}")
                    return text
                time.sleep(1)
                continue
        
        return text

    def create_article_directory(self, title):
        """为每篇文章创建独立的目录"""
        # 使用标题的MD5作为目录名，避免文件名问题
        dir_name = title.replace(' ', '_').replace(':', '_')
        full_path = os.path.join(self.base_download_dir, dir_name)
        os.makedirs(full_path, exist_ok=True)
        return full_path

    def save_to_excel(self, data):
        """保存数据到Excel文件"""
        excel_path = os.path.join(self.base_download_dir, 'assets_data.xlsx')
        try:
            # 准备数据
            df_row = {
                'title': data.get('title', ''),
                'url': data.get('url', ''),
                'file_path': data.get('file_path', ''),  # 使用get方法安全获取
                'content': data.get('content', ''),
                'translated_content': data.get('translated_content', '')
            }
            
            # 如果文件存在，读取现有数据
            if os.path.exists(excel_path):
                df_existing = pd.read_excel(excel_path)
                df_new = pd.DataFrame([df_row])
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            else:
                df_combined = pd.DataFrame([df_row])
            
            # 保存到Excel
            df_combined.to_excel(excel_path, index=False)
            self.logger.info(f"数据已保存到Excel: {excel_path}")
        except Exception as e:
            self.logger.error(f"保存Excel时出错: {e}")
            raise  # 重新抛出异常以便调试

    def download_image(self, img_url, save_dir):
        if not img_url:
            return None
            
        try:
            # 创建图片文件名
            img_filename = os.path.join(save_dir, 'thumbnail' + os.path.splitext(urllib.parse.urlparse(img_url).path)[1])
            
            # 检查文件是否已存在
            if os.path.exists(img_filename):
                self.logger.info(f"图片已存在: {img_filename}")
                return img_filename

            # 尝试直接下载
            try:
                direct_session = requests.Session()
                direct_session.headers = self.session.headers
                direct_session.verify = self.session.verify
                response = direct_session.get(img_url, timeout=30)
                response.raise_for_status()
            except Exception as e:
                self.logger.warning(f"直接下载失败，尝试使用代理: {e}")
                # 使用代理重试
                response = self.session.get(img_url, timeout=30)
                response.raise_for_status()
            
            with open(img_filename, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"已下载图片: {img_filename}")
            return img_filename
            
        except Exception as e:
            self.logger.error(f"下载图片失败 {img_url}: {e}")
            return None

    def get_page_content(self, url, timeout=30):
        """获取页面内容，先尝试直连，失败后使用代理"""
        try:
            # 尝试直接连接
            direct_session = requests.Session()
            direct_session.headers = self.session.headers
            direct_session.verify = self.session.verify
            response = direct_session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.logger.warning(f"直接访问失败，尝试使用代理: {e}")
            # 使用代理重试
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text

    def parse_article(self, html_content, url, custom_title=None, file_path=None):
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
            
            return {
                'title': title,
                'url': url,
                'file_path': file_path,  # 添加文件路径
                'img_url': img_url,
                'content': content_text,
                'translated_content': translated_content
            }
            
        except Exception as e:
            self.logger.error(f"解析文章失败: {e}")
            return None

    def save_article(self, article_data):
        if not article_data:
            return False
            
        try:
            # 为文章创建独立目录
            article_dir = self.create_article_directory(article_data['title'])
            
            # 下载图片
            img_filename = self.download_image(article_data['img_url'], article_dir)
            
            # 保存原文
            original_content_filename = os.path.join(article_dir, 'original.txt')
            with open(original_content_filename, 'w', encoding='utf-8') as f:
                f.write(f"Title: {article_data['title']}\n")
                f.write(f"URL: {article_data['url']}\n")
                f.write(f"Image: {article_data['img_url']}\n\n")
                f.write("Content:\n")
                f.write(article_data['content'])
            
            # 保存翻译后的内容
            translated_content_filename = os.path.join(article_dir, 'translated.txt')
            with open(translated_content_filename, 'w', encoding='utf-8') as f:
                f.write(f"标题: {article_data['title']}\n")
                f.write(f"URL: {article_data['url']}\n")
                f.write(f"图片: {article_data['img_url']}\n\n")
                f.write("正文内容:\n")
                f.write(article_data['translated_content'])
            
            # 保存元数据
            metadata_filename = os.path.join(article_dir, 'metadata.json')
            with open(metadata_filename, 'w', encoding='utf-8') as f:
                json.dump(article_data, f, ensure_ascii=False, indent=2)
            
            # 保存数据到Excel
            data = {
                'title': article_data['title'],
                'content': article_data['content'],
                'translated_content': article_data['translated_content'],
                'image_path': img_filename,
                'url': article_data['url'],
                'save_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            self.save_to_excel(data)
            
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
            html_content = self.get_page_content(url)
            article_data = self.parse_article(html_content, url)
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

    def can_fetch(self, url):
        try:
            return self.robots.can_fetch("*", url)
        except Exception:
            return True

# 使用示例
if __name__ == "__main__":
    base_url = "https://unityassets4free.com/"  # 替换为目标网站
    urls = [
        "https://unityassets4free.com/tile-world-match/",  # 替换为实际的URL列表
        "https://unityassets4free.com/arcade-ultimate-vehicles-pack-low-poly-cars/",
        # ... 更多URL
    ]
    
    scraper = WebsiteScraper(base_url, max_workers=3, delay=1, disable_ssl_verification=True)
    results = scraper.scrape_urls(urls)
    
    print(f"成功处理 {len(results)} 个页面")
    
    # 保存总结报告
    with open(os.path.join(scraper.base_download_dir, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)