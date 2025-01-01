import os
from handlefilename import clean_file_names
from googleserach import google_search
from assets4free import WebsiteScraper
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from urllib3.util.ssl_ import create_urllib3_context
import warnings
from requests.exceptions import SSLError
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# 忽略 SSL 警告（如果需要禁用 SSL 验证）
warnings.simplefilter("ignore", InsecureRequestWarning)


# 自定义 TLS 适配器以强制使用 TLS 1.2
class TLSAdapter(HTTPAdapter):
    def __init__(self, tls_version=None, **kwargs):
        self.tls_version = tls_version
        self.ssl_context = create_urllib3_context()
        if self.tls_version:
            self.ssl_context.options |= self.tls_version
        super().__init__(**kwargs)


def process_single_asset(directory, file_info, disable_ssl_verification=False):
    """
    处理单个资源文件
    :param directory: 资源文件所在目录
    :param file_info: 文件信息字典
    :param disable_ssl_verification: 是否禁用 SSL 验证（默认 False）
    """
    print(f"处理文件: {file_info['original_name']}")
    print(f"清理后的名称: {file_info['cleaned_name']}")

    # website = "site:assetstore.unity.com "
    website = "site:unityassets4free.com "
    # 1. 使用 Google 搜索获取标题和链接
    search_query = f"{website}{file_info['cleaned_name']}"
    search_result = google_search(search_query)

    if not search_result:
        print("未找到相关搜索结果")
        return False

    print(f"找到资源: {search_result['title']}")
    print(f"资源链接: {search_result['link']}")

    # 2. 使用 WebsiteScraper 处理内容
    scraper = WebsiteScraper(base_url="https://unityassets4free.com/")

    # 配置请求会话（添加自定义 TLS 支持）
    session = scraper.session
    retries = Retry(total=5, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
    adapter = TLSAdapter()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    # 配置 Clash 代理
    proxies = {
        "http": "http://127.0.0.1:2612",  # Clash 默认 HTTP 代理端口
        "https": "http://127.0.0.1:2612",  # Clash 默认 HTTPS 代理端口
    }

    try:
        # 获取网页内容
        response = session.get(
            search_result['link'],
            timeout=10,
            proxies=proxies,  # 设置代理
            verify=not disable_ssl_verification  # 是否禁用 SSL 验证
        )
        if response.status_code != 200:
            print(f"无法访问资源页面, 状态码: {response.status_code}")
            return False

        # 解析文章内容，使用 Google 搜索结果的标题
        article_data = scraper.parse_article(
            response.text,
            search_result['link'],
            custom_title=search_result['title'],
            file_path=file_info['full_path']
        )

        if not article_data:
            print("解析文章失败")
            return False

        # 保存文章内容
        if scraper.save_article(article_data):
            print("成功保存文章内容")
            return True
        else:
            print("保存文章失败")
            return False
    except SSLError as e:
        print(f"SSL 错误: {e}")
        return False
    except Exception as e:
        print(f"请求时发生错误: {e}")
        return False

def process_assets(directory, file_indices=None, disable_ssl_verification=False):
    """
    处理资源文件的主函数
    :param directory: 资源文件所在目录
    :param file_indices: 要处理的文件索引列表（按文件名排序后）
    :param disable_ssl_verification: 是否禁用 SSL 验证（默认 False）
    """
    # 1. 获取并清理所有文件名
    all_files = clean_file_names(directory)
    if not isinstance(all_files, list):
        print("错误：clean_file_names 没有返回文件列表")
        return
        
    if not all_files:
        print("目录中没有找到文件")
        return

    print("\n所有文件:")
    for i, file_info in enumerate(all_files):
        print(f"{i}. {file_info['original_name']} -> {file_info['cleaned_name']}")

    # 如果没有指定索引，默认处理第一个文件
    if file_indices is None:
        file_indices = [0]
    
    print(f"\n要处理的文件索引: {file_indices}")
    
    # 确保索引有效
    valid_indices = [i for i in file_indices if 0 <= i < len(all_files)]
    if not valid_indices:
        print("没有有效的文件索引")
        return

    print(f"有效的文件索引: {valid_indices}")

    # 处理每个指定的文件
    results = []
    for idx in valid_indices:
        print(f"\n开始处理第 {idx + 1} 个文件:")
        file_info = all_files[idx]
        print(f"文件信息: {file_info}")
        success = process_single_asset(directory, file_info, disable_ssl_verification)
        results.append({
            'index': idx,
            'file': file_info['original_name'],
            'success': success
        })

    # 打印处理结果摘要
    print("\n处理结果摘要:")
    for result in results:
        status = "成功" if result['success'] else "失败"
        print(f"文件 {result['file']} (索引 {result['index']}): {status}")

if __name__ == "__main__":
    # 示例用法
    target_directory = r"F:\0游戏教程\0tele"  # 替换为实际目录
    process_assets(target_directory, file_indices=[5, 6], disable_ssl_verification=True)  # 处理多个文件