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

class BaseCrawler:
    def __init__(self, base_url, max_workers=3, delay=1, disable_ssl_verification=False, use_proxy=False, proxy_url=None):
        self.base_url = base_url
        self.max_workers = max_workers
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # 配置代理
        if use_proxy:
            if proxy_url:
                self.session.proxies = {
                    "http": proxy_url,
                    "https": proxy_url,
                }
            else:
                self.logger.error("代理地址未配置")
                raise ValueError("代理地址未配置")
        else:
            self.session.proxies = {}  # 确保完全禁用代理
        
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
                chunks = [text[i:i+500] for i in range(0, len(text), 500)]
                translated_chunks = []
                
                for chunk in chunks:
                    translated = self.translator.translate(chunk)
                    translated_chunks.append(translated)
                    time.sleep(0.5)
                
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
        dir_name = title.replace(' ', '_').replace(':', '_')
        full_path = os.path.join(self.base_download_dir, dir_name)
        os.makedirs(full_path, exist_ok=True)
        return full_path

    def save_to_excel(self, data):
        """保存数据到Excel文件"""
        excel_path = os.path.join(self.base_download_dir, 'assets_data.xlsx')
        try:
            df_row = {
                'title': data.get('title', ''),
                'url': data.get('url', ''),
                'file_path': data.get('file_path', ''),
                'file_name': data.get('file_name', ''),
                'original_content': data.get('content', ''),
                'translated_content': data.get('translated_content', ''),
                'image_path': data.get('image_path', ''),
                'save_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            if os.path.exists(excel_path):
                df_existing = pd.read_excel(excel_path)
                df_new = pd.DataFrame([df_row])
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            else:
                df_combined = pd.DataFrame([df_row])
            
            df_combined.to_excel(excel_path, index=False)
            self.logger.info(f"数据已保存到Excel: {excel_path}")
        except Exception as e:
            self.logger.error(f"保存Excel时出错: {e}")
            raise

    def download_image(self, img_url, save_dir):
        """下载图片"""
        if not img_url:
            return None
            
        try:
            img_filename = os.path.join(save_dir, 'thumbnail' + os.path.splitext(urllib.parse.urlparse(img_url).path)[1])
            
            if os.path.exists(img_filename):
                self.logger.info(f"图片已存在: {img_filename}")
                return img_filename

            try:
                direct_session = requests.Session()
                direct_session.headers = self.session.headers
                direct_session.verify = self.session.verify
                response = direct_session.get(img_url, timeout=30)
                response.raise_for_status()
            except Exception as e:
                self.logger.warning(f"直接下载失败，尝试使用代理: {e}")
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
        """获取页面内容"""
        try:
            direct_session = requests.Session()
            direct_session.headers = self.session.headers
            direct_session.verify = self.session.verify
            response = direct_session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.logger.warning(f"直接访问失败，尝试使用代理: {e}")
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text

    def parse_article(self, html_content, url):
        """解析文章，这是一个需要被子类重写的基础方法"""
        raise NotImplementedError("子类必须实现parse_article方法")

    def crawl_urls(self, urls):
        """批量爬取URLs"""
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(self.crawl_single_url, url): url for url in urls}
            for future in future_to_url:
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    self.logger.error(f"处理URL时出错: {e}")
                time.sleep(self.delay)
        return results

    def crawl_single_url(self, url):
        """爬取单个URL，这是一个需要被子类重写的基础方法"""
        raise NotImplementedError("子类必须实现crawl_single_url方法")

    def save_article(self, article_data):
        """保存文章数据到文件系统和Excel"""
        if not article_data:
            return False
            
        try:
            # 为文章创建独立目录
            article_dir = self.create_article_directory(article_data['title'])
            
            # 下载图片并获取绝对路径
            img_filename = self.download_image(article_data.get('img_url'), article_dir)
            
            # 保存原文
            original_content_filename = os.path.join(article_dir, 'original.txt')
            with open(original_content_filename, 'w', encoding='utf-8') as f:
                f.write(f"Title: {article_data['title']}\n")
                f.write(f"URL: {article_data['url']}\n")
                f.write(f"Image: {article_data.get('img_url', '')}\n\n")
                f.write("Content:\n")
                f.write(article_data.get('content', ''))
            
            # 保存翻译后的内容
            translated_content_filename = os.path.join(article_dir, 'translated.txt')
            with open(translated_content_filename, 'w', encoding='utf-8') as f:
                f.write(f"标题: {article_data['title']}\n")
                f.write(f"URL: {article_data['url']}\n")
                f.write(f"图片: {article_data.get('img_url', '')}\n\n")
                f.write("正文内容:\n")
                f.write(article_data.get('translated_content', ''))
            
            # 保存元数据
            metadata_filename = os.path.join(article_dir, 'metadata.json')
            with open(metadata_filename, 'w', encoding='utf-8') as f:
                json.dump(article_data, f, ensure_ascii=False, indent=2)
            
            # 保存数据到Excel
            data = {
                'title': article_data['title'],
                'url': article_data['url'],
                'file_path': article_data.get('file_path', ''),
                'file_name': article_data.get('file_name', ''),
                'content': article_data.get('content', ''),
                'translated_content': article_data.get('translated_content', ''),
                'image_path': os.path.abspath(img_filename) if img_filename else ''
            }
            
            self.save_to_excel(data)
            return True
            
        except Exception as e:
            self.logger.error(f"保存文章失败: {e}")
            return False
