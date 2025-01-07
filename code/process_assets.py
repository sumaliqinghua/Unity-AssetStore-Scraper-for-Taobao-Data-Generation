import os
from handlefilename import clean_file_names
from googleserach import google_search
from assets4free_crawler import Assets4FreeCrawler
from taobao_crawler import TaoBaoCrawler
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


def get_crawler_instance(crawler_type=None, max_workers=3, delay=1, disable_ssl_verification=False):
    """
    获取爬虫实例
    :param crawler_type: 爬虫类型，可以是 'assets4free' 或 'taobao'
    :return: 爬虫实例
    """
    if crawler_type is None:
        print("\n选择爬虫类型：")
        print("1. Assets4Free爬虫")
        print("2. 淘宝爬虫")
        choice = input("请选择爬虫类型 (1/2): ").strip()
        crawler_type = 'assets4free' if choice == '1' else 'taobao'
    
    if crawler_type == 'assets4free':
        return Assets4FreeCrawler(max_workers=max_workers, delay=delay)
    else:
        return TaoBaoCrawler(max_workers=max_workers, delay=delay)


def process_single_asset(directory, file_info, disable_ssl_verification=False):
    """
    处理单个资源文件
    :param directory: 资源文件所在目录
    :param file_info: 文件信息字典
    :param disable_ssl_verification: 是否禁用 SSL 验证（默认 False）
    """
    print(f"处理文件: {file_info['original_name']}")
    print(f"清理后的名称: {file_info['cleaned_name']}")

    # 选择搜索网站
    print("\n选择搜索网站：")
    print("1. Unity Asset Store")
    print("2. Unity Assets 4 Free")
    site_choice = input("请选择搜索网站 (1/2): ").strip()
    website = "site:assetstore.unity.com " if site_choice == '1' else "site:unityassets4free.com "
    crawler_type = 'taobao' if site_choice == '1' else 'assets4free'

    # 1. 使用 Google 搜索获取标题和链接
    while True:
        search_query = f"{website}{file_info['cleaned_name']}"
        search_query = search_query.replace("_", " ")
        search_results = google_search(search_query)

        if not search_results:
            print(f"未找到相关搜索结果 {search_query}")
            user_input = input("请输入新的搜索词（直接回车退出）: ")
            if not user_input:
                return False
            file_info['cleaned_name'] = user_input
            continue

        # 显示搜索结果并让用户确认
        print("\n搜索结果：")
        for i, result in enumerate(search_results, 1):
            print(f"{i}. 标题: {result['title']}")
            print(f"   链接: {result['link']}\n")
        
        choice = input("请选择要使用的结果编号（输入数字），输入n重新搜索，直接回车退出：").strip()
        if not choice:
            return False
        if choice.lower() == 'n':
            user_input = input("请输入新的搜索词: ")
            if user_input:
                file_info['cleaned_name'] = user_input
                continue
            return False
        
        try:
            selected_index = int(choice) - 1
            if 0 <= selected_index < len(search_results):
                selected_result = search_results[selected_index]
                break
            else:
                print("无效的选择，请重试")
                continue
        except ValueError:
            print("无效的输入，请重试")
            continue

    # 2. 获取爬虫实例并抓取页面
    crawler = get_crawler_instance(crawler_type=crawler_type)
    
    try:
        # 3. 下载并解析页面
        response = crawler.session.get(selected_result['link'], verify=not disable_ssl_verification)
        response.raise_for_status()
        
        # 4. 解析页面内容
        parsed_content = crawler.parse_article(response.text, selected_result['link'], 
                                            custom_title=selected_result['title'],
                                            file_path=file_info['full_path'])
        
        if parsed_content:
            print("成功获取页面内容")
            return True
        else:
            print("无法解析页面内容")
            return False
            
    except Exception as e:
        print(f"处理过程中出错: {str(e)}")
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

    # 创建爬虫实例（这里先创建一个，后面根据需要可能会创建新的）
    crawler = None
    last_crawler_type = None

    # 处理每个指定的文件
    results = []
    for idx in valid_indices:
        print(f"\n开始处理第 {idx + 1} 个文件:")
        file_info = all_files[idx]
        print(f"文件信息: {file_info}")
        
        # 选择搜索网站
        print("\n选择搜索网站：")
        print("1. Unity Asset Store")
        print("2. Unity Assets 4 Free")
        site_choice = input("请选择搜索网站 (1/2): ").strip()
        website = "site:assetstore.unity.com " if site_choice == '1' else "site:unityassets4free.com "
        crawler_type = 'taobao' if site_choice == '1' else 'assets4free'
        
        # 如果爬虫类型改变，创建新的爬虫实例
        if crawler_type != last_crawler_type:
            crawler = get_crawler_instance(crawler_type=crawler_type)
            last_crawler_type = crawler_type

        # 1. 使用 Google 搜索获取标题和链接
        while True:
            search_query = f"{website}{file_info['cleaned_name']}"
            search_query = search_query.replace("_", " ")
            search_results = google_search(search_query)

            if not search_results:
                print(f"未找到相关搜索结果 {search_query}")
                user_input = input("请输入新的搜索词（直接回车退出）: ")
                if not user_input:
                    break
                file_info['cleaned_name'] = user_input
                continue

            # 显示搜索结果并让用户确认
            print("\n搜索结果：")
            for i, result in enumerate(search_results, 1):
                print(f"{i}. 标题: {result['title']}")
                print(f"   链接: {result['link']}\n")
            
            choice = input("请选择要使用的结果编号（输入数字），输入n重新搜索，直接回车退出：").strip()
            if not choice:
                break
            if choice.lower() == 'n':
                user_input = input("请输入新的搜索词: ")
                if user_input:
                    file_info['cleaned_name'] = user_input
                    continue
                break
            
            try:
                selected_index = int(choice) - 1
                if 0 <= selected_index < len(search_results):
                    selected_result = search_results[selected_index]
                    
                    try:
                        # 下载并解析页面
                        response = crawler.session.get(selected_result['link'], verify=not disable_ssl_verification)
                        response.raise_for_status()
                        
                        # 解析页面内容
                        parsed_content = crawler.parse_article(response.text, selected_result['link'], 
                                                            custom_title=selected_result['title'],
                                                            file_path=file_info['full_path'])
                        
                        if parsed_content:
                            print("成功获取页面内容")
                            results.append(parsed_content)
                        else:
                            print("无法解析页面内容")
                    except Exception as e:
                        print(f"处理过程中出错: {str(e)}")
                    
                    break
                else:
                    print("无效的选择，请重试")
                    continue
            except ValueError:
                print("无效的输入，请重试")
                continue

    # 打印处理结果摘要
    print("\n处理结果摘要:")
    for i, result in enumerate(results):
        print(f"文件 {i + 1}: {result.get('title', '未知标题')}")
    
    # 如果有结果且使用的是TaoBaoCrawler，保存到Excel
    if results and isinstance(crawler, TaoBaoCrawler):
        crawler.results = results
        crawler.save_to_excel()


if __name__ == "__main__":
    # 示例用法
    target_directory = r"F:\0游戏教程\0tele"  # 替换为实际目录
    process_assets(target_directory, file_indices=[6], disable_ssl_verification=True)  # 处理多个文件