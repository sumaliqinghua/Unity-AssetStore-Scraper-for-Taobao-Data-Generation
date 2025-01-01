import os
import re

# 文件路径
directory = r"F:\0游戏教程\0tele"

# 获取文件名的函数
def clean_file_names(directory, file_index=0):
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
    
    # 如果列表不为空且索引有效，返回指定索引的文件信息
    if files_info and 0 <= file_index < len(files_info):
        return files_info[file_index]
    elif files_info:
        return files_info[0]  # 如果索引无效但列表不为空，返回第一个文件
    else:
        return None  # 如果没有文件，返回None

# 调用函数并打印结果
cleaned_files = clean_file_names(directory, file_index=1)
if cleaned_files:
    print("清理后的文件名：")
    print(cleaned_files['cleaned_name'])
    print("原始文件名：")
    print(cleaned_files['original_name'])
    print("文件路径：")
    print(cleaned_files['full_path'])
else:
    print("没有找到文件。")