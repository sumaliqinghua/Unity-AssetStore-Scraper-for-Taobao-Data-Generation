import os
import re

def clean_file_names(directory, file_index=None):
    """
    获取并清理文件名
    :param directory: 文件目录路径
    :param file_index: 如果是整数，返回单个文件信息；如果是None，返回所有文件信息
    :return: 单个文件信息字典或文件信息字典列表
    """
    # 列表存储最终的文件名和路径
    files_info = []
    
    # 遍历路径中的所有文件
    for file_name in os.listdir(directory):
        # 获取文件的完整路径
        full_path = os.path.join(directory, file_name)
        
        # 确保是文件而不是子文件夹
        if os.path.isfile(full_path):
            # 去掉文件后缀
            name_without_extension = os.path.splitext(file_name)[0]
            # 删除从 v1.6.3 或类似模式开始的内容
            cleaned_name = re.split(r'v\d+(\.\d+)*', name_without_extension)[0]  # 按版本号分割，保留前面部分
            cleaned_name = cleaned_name.strip()  # 去掉多余的空格
            files_info.append({
                'cleaned_name': cleaned_name,
                'original_name': file_name,
                'full_path': full_path
            })
    
    # 按文件名排序
    files_info.sort(key=lambda x: x['original_name'])
    
    # 如果没有文件，返回空列表
    if not files_info:
        return [] if file_index is None else None
        
    # 如果指定了索引，返回单个文件信息
    if isinstance(file_index, int):
        if 0 <= file_index < len(files_info):
            return files_info[file_index]
        return None  # 如果索引无效，返回None
    
    # 否则返回所有文件信息
    return files_info

if __name__ == "__main__":
    # 示例用法
    directory = r"F:\0游戏教程\0tele"
    
    # 获取所有文件
    all_files = clean_file_names(directory)
    print("\n所有文件:")
    for i, file_info in enumerate(all_files):
        print(f"{i}. {file_info['original_name']} -> {file_info['cleaned_name']}")
    
    # 获取特定文件
    file_info = clean_file_names(directory, file_index=1)
    if file_info:
        print(f"\n第2个文件:")
        print(f"清理后的名称: {file_info['cleaned_name']}")
        print(f"原始文件名: {file_info['original_name']}")
        print(f"文件路径: {file_info['full_path']}")