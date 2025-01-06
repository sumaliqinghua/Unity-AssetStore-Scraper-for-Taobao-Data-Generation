from base_crawler import BaseCrawler
from bs4 import BeautifulSoup

class TaoBaoCrawler(BaseCrawler):
    def __init__(self, max_workers=3, delay=1):
        super().__init__(
            base_url="https://www.assetstore.unity.com/",  # 设置一个基础URL
            max_workers=max_workers,
            delay=delay,
            use_proxy=True,  # 使用代理
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
            str: Concatenated text from the divs, separated by newlines
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        texts = []
        
        # First description in _3MR2i
        first_desc = soup.find('div', class_='_3MR2i').find('div', class_='_1_3uP _1rkJa')
        if first_desc:
            texts.append(first_desc.get_text(strip=True))
        
        # Find all _3lKf4 divs (they contain the other descriptions)
        description_containers = soup.find_all('div', class_='_3lKf4')
        
        for container in description_containers:
            # Look for _1RlcV div inside each container
            content_div = container.find('div', class_='_1RlcV')
            if content_div:
                desc = content_div.find('div', class_='_1_3uP _1rkJa')
                if desc:
                    texts.append(desc.get_text(strip=True))
        
        return '\n'.join(texts)

# 使用示例
if __name__ == "__main__":
    crawler = TaoBaoCrawler()
    
    # 从文件读取HTML内容
    with open('code/a.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # 提取文本
    result = crawler.extract_description_text(html_content)
    print(result)
