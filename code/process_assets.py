import os
from handlefilename import clean_file_names
from googleserach import google_search
from assets4free import WebsiteScraper

def process_assets(directory, file_index=0):
    """
    处理资源文件的主函数
    :param directory: 资源文件所在目录
    :param file_index: 要处理的文件索引（按文件名排序后）
    """
    # 1. 获取并清理文件名
    file_info = clean_file_names(directory, file_index)
    if not file_info:
        print("没有找到文件或索引无效")
        return

    print(f"处理文件: {file_info['original_name']}")
    print(f"清理后的名称: {file_info['cleaned_name']}")

    # 2. 使用Google搜索获取标题和链接
    search_query = f"site:assetstore.unity.com {file_info['cleaned_name']}"
    search_result = google_search(search_query)
    
    if not search_result:
        print("未找到相关搜索结果")
        return

    print(f"找到资源: {search_result['title']}")
    print(f"资源链接: {search_result['link']}")

    # 3. 使用WebsiteScraper处理内容
    scraper = WebsiteScraper(base_url="https://unityassets4free.com/")
    
    # 获取网页内容
    response = scraper.session.get(search_result['link'])
    if response.status_code != 200:
        print("无法访问资源页面")
        return

    # 解析文章内容，使用Google搜索结果的标题
    article_data = scraper.parse_article(
        response.text,
        search_result['link'],
        custom_title=search_result['title'],
        file_path=file_info['full_path']
    )

    if not article_data:
        print("解析文章失败")
        return

    # 保存文章内容
    if scraper.save_article(article_data):
        print("成功保存文章内容")
    else:
        print("保存文章失败")

if __name__ == "__main__":
    # 示例用法
    target_directory = r"F:\0游戏教程\0tele"  # 替换为实际目录
    process_assets(target_directory, file_index=0)  # 处理第一个文件
