import os
from handlefilename import clean_file_names
from googleserach import google_search
from assets4free_crawler import Assets4FreeCrawler
from unityasset_crawler import UnityAssetCrawler
from input_utils import select_with_timeout
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from urllib3.util.ssl_ import create_urllib3_context
import warnings
from requests.exceptions import SSLError
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import threading
import msvcrt
import time
import pandas as pd
from openpyxl import load_workbook

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
    :param crawler_type: 爬虫类型，可以是 'assets4free' 或 'unityasset'
    :return: 爬虫实例
    """
    if crawler_type is None:
        print("\n选择爬虫类型：")
        print("1. Assets4Free爬虫")
        print("2. UnityAsset爬虫")
        choice = select_with_timeout("请选择爬虫类型 (1/2): ").strip()
        crawler_type = 'assets4free' if choice == '1' else 'unityasset'
    
    if crawler_type == 'assets4free':
        return Assets4FreeCrawler(max_workers=max_workers, delay=delay)
    else:
        return UnityAssetCrawler(max_workers=max_workers, delay=delay)

def save_to_excel(results, excel_path):
    """
    将搜索结果保存到Excel文件，支持追加模式
    :param results: 搜索结果字典
    :param excel_path: Excel文件路径
    """
    # 准备新数据
    data = []
    for file_name, info in results.items():
        result = info['selected_result']  # 只保存用户选择的结果
        data.append({
            'file_name': file_name,
            'title': result['title'],
            'link': result['link'],
            'crawler_type': info['crawler_type']
        })
    
    # 创建DataFrame
    new_df = pd.DataFrame(data)
    
    try:
        # 尝试读取现有文件
        if os.path.exists(excel_path):
            existing_df = pd.read_excel(excel_path)
            # 合并现有数据和新数据
            df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            df = new_df
        
        # 保存到Excel
        df.to_excel(excel_path, index=False)
        print(f"搜索结果已保存到: {excel_path}")
        
    except Exception as e:
        print(f"保存Excel时出错: {str(e)}")
        # 如果出错，尝试直接保存新数据
        new_df.to_excel(excel_path, index=False)
        print(f"已创建新的Excel文件: {excel_path}")

def move_file_to_destination(file_path):
    """
    将文件移动到指定目录
    :param file_path: 原文件路径
    :return: 新的文件路径，如果移动失败则返回原路径
    """
    if not file_path or not os.path.exists(file_path):
        return file_path

    try:
        # 创建目标目录
        dest_dir = r"F:\BaiduNetdiskDownload\0moved"
        os.makedirs(dest_dir, exist_ok=True)
        
        # 构建目标路径
        file_name = os.path.basename(file_path)
        new_path = os.path.join(dest_dir, file_name)
        
        # 如果目标文件已存在，添加数字后缀
        base_name, ext = os.path.splitext(file_name)
        counter = 1
        while os.path.exists(new_path):
            new_path = os.path.join(dest_dir, f"{base_name}_{counter}{ext}")
            counter += 1
        
        # 移动文件
        os.rename(file_path, new_path)
        print(f"文件已移动: {file_path} -> {new_path}")
        return new_path
        
    except Exception as e:
        print(f"移动文件失败: {str(e)}")
        return file_path

def google_search_step(directory, file_indices=None):
    """
    执行Google搜索步骤，将结果保存到Excel
    :param directory: 资源文件所在目录
    :param file_indices: 要处理的文件索引列表
    :return: 搜索结果的字典，键为文件名，值为搜索结果列表
    """
    # 确保downloads目录存在
    downloads_dir = os.path.abspath('downloads')
    os.makedirs(downloads_dir, exist_ok=True)
    excel_path = os.path.join(downloads_dir, 'search_results.xlsx')
    
    all_files = clean_file_names(directory)
    if not isinstance(all_files, list) or not all_files:
        print("错误：没有找到有效文件")
        return None
    
    if file_indices is None:
        file_indices = [0]
    
    valid_indices = [i for i in file_indices if 0 <= i < len(all_files)]
    if not valid_indices:
        print("没有有效的文件索引")
        return None

    # 询问是否在保存后移动文件
    print("\n是否在保存搜索结果后移动原文件？")
    print("1. 是")
    print("2. 否")
    move_files = select_with_timeout("请选择 (1/2): ", "2").strip() == "1"

    results = {}
    moved_files = []  # 记录已移动的文件
    
    for idx in valid_indices:
        file_info = all_files[idx]
        print(f"\n处理文件: {file_info['cleaned_name']}")
        
        print("\n选择搜索网站：")
        print("1. Unity Asset Store")
        print("2. Unity Assets 4 Free")
        site_choice = select_with_timeout("请选择搜索网站 (1/2)", "1")
        website = "site:assetstore.unity.com " if site_choice == '1' else "site:unityassets4free.com "
        crawler_type = 'unityasset' if site_choice == '1' else 'assets4free'
        
        search_query = website + file_info['cleaned_name']
        search_results = google_search(search_query)
        
        if search_results:
            # 显示搜索结果并让用户选择
            print("\n搜索结果：")
            for i, result in enumerate(search_results, 1):
                print(f"{i}. 标题: {result['title']}")
                print(f"   链接: {result['link']}\n")
            
            while True:
                choice = select_with_timeout("请选择要保存的结果编号（输入数字），输入n跳过此文件：", "1")
                if choice.lower() == 'n':
                    print(f"已跳过文件: {file_info['cleaned_name']}")
                    break
                    
                try:
                    selected_index = int(choice) - 1
                    if 0 <= selected_index < len(search_results):
                        results[file_info['cleaned_name']] = {
                            'selected_result': search_results[selected_index],
                            'crawler_type': crawler_type
                        }
                        # 如果选择了移动文件并成功保存了搜索结果
                        if move_files:
                            moved_files.append(file_info['full_path'])
                        break
                    else:
                        print("无效的选择，请重试")
                except ValueError:
                    print("无效的输入，请重试")
    
    # 保存结果到Excel
    if results:
        save_to_excel(results, excel_path)
        
        # 如果选择了移动文件，则移动所有已保存结果的文件
        if move_files and moved_files:
            print("\n开始移动文件...")
            for file_path in moved_files:
                move_file_to_destination(file_path)
    
    return results

def crawler_step(directory, file_indices=None, disable_ssl_verification=False, search_results=None):
    """
    执行爬虫步骤，获取描述并保存结果
    :param directory: 资源文件所在目录
    :param file_indices: 要处理的文件索引列表
    :param disable_ssl_verification: 是否禁用SSL验证
    :param search_results: Google搜索的结果字典，如果为None则尝试从Excel读取
    """
    all_files = clean_file_names(directory)
    if not isinstance(all_files, list) or not all_files:
        print("错误：没有找到有效文件")
        return
    
    if file_indices is None:
        file_indices = [0]
    
    valid_indices = [i for i in file_indices if 0 <= i < len(all_files)]
    if not valid_indices:
        print("没有有效的文件索引")
        return

    # 如果没有提供搜索结果，尝试从Excel读取
    if search_results is None:
        excel_path = os.path.join(directory, 'search_results.xlsx')
        if os.path.exists(excel_path):
            try:
                search_results = read_from_excel(excel_path)
            except Exception as e:
                print(f"读取Excel文件失败: {str(e)}")
                return
        else:
            print(f"找不到搜索结果文件: {excel_path}")
            return

    crawler = None
    last_crawler_type = None
    results = []
    
    for idx in valid_indices:
        file_info = all_files[idx]
        file_name = file_info['cleaned_name']
        
        if file_name not in search_results:
            print(f"\n跳过文件 {file_name}: 没有找到对应的搜索结果")
            continue
            
        print(f"\n处理文件: {file_name}")
        
        # 使用搜索结果中的爬虫类型
        crawler_type = search_results[file_name]['crawler_type']
        
        if crawler_type != last_crawler_type:
            crawler = get_crawler_instance(crawler_type=crawler_type)
            last_crawler_type = crawler_type
        
        # 使用搜索结果中的URL
        success = False
        for result in search_results[file_name]['search_results']:
            try:
                # 获取页面内容
                response = crawler.session.get(result['link'], verify=not disable_ssl_verification)
                response.raise_for_status()
                
                # 解析页面内容
                parsed_content = crawler.parse_article(
                    response.text,
                    result['link'],
                    custom_title=result['title'],
                    file_path=file_info['full_path']
                )
                
                if parsed_content:
                    print(f"成功处理URL: {result['link']}")
                    results.append(parsed_content)
                    success = True
                    break
                
            except Exception as e:
                print(f"处理URL时出错: {str(e)}")
                continue
        
        if not success:
            print(f"无法成功处理文件 {file_name} 的任何URL")
    
    # 如果有结果且使用的是UnityAssetCrawler，保存到Excel
    if results and isinstance(crawler, UnityAssetCrawler):
        crawler.results = results
        crawler.save_to_excel()

def read_from_excel(excel_path):
    """
    从Excel文件读取搜索结果
    :param excel_path: Excel文件路径
    :return: 搜索结果字典
    """
    # 读取Excel文件
    df = pd.read_excel(excel_path)
    
    # 转换为字典格式
    results = {}
    for _, row in df.iterrows():
        file_name = row['file_name']
        if file_name not in results:
            results[file_name] = {
                'search_results': [],
                'crawler_type': row['crawler_type']
            }
        
        # 将每个结果添加到search_results列表中
        results[file_name]['search_results'].append({
            'title': row['title'],
            'link': row['link']
        })
    
    return results

def process_assets(directory, file_indices=None, disable_ssl_verification=False):
    """
    处理资源文件的主函数，现在通过调用google_search_step和crawler_step来完成
    :param directory: 资源文件所在目录
    :param file_indices: 要处理的文件索引列表
    :param disable_ssl_verification: 是否禁用SSL验证
    """
    # 步骤1：执行Google搜索
    print("\n=== 步骤1：执行Google搜索 ===")
    search_results = google_search_step(directory, file_indices)
    if not search_results:
        print("Google搜索步骤失败，终止处理")
        return
        
    # 步骤2：执行爬虫
    print("\n=== 步骤2：执行爬虫获取资源信息 ===")
    crawler_step(directory, file_indices, disable_ssl_verification, search_results)

if __name__ == "__main__":
    target_directory = r"F:\0游戏教程\0tele"  # 替换为实际目录
    
    print("\n选择执行模式：")
    print("1. 仅执行Google搜索并保存结果")
    print("2. 仅执行爬虫获取描述（使用已保存的搜索结果）")
    print("3. 执行完整流程（搜索+爬虫）")
    
    mode = select_with_timeout("请选择执行模式 (1/2/3): ", "3").strip()
    file_indices = [1]  # 可以根据需要修改要处理的文件索引
    
    if mode == "1":
        google_search_step(target_directory, file_indices)
    elif mode == "2":
        crawler_step(target_directory, file_indices, disable_ssl_verification=True)
    else:
        process_assets(target_directory, file_indices, disable_ssl_verification=True)