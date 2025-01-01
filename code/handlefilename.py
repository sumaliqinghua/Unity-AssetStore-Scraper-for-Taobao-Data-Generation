import os
import re

# 文件路径
directory = r"F:\0游戏教程\0tele"

# 获取文件名的函数
def clean_file_names(directory):
    # 列表存储最终的文件名
    cleaned_names = []
    
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
            cleaned_names.append(cleaned_name)
    
    return cleaned_names

# 调用函数并打印结果
cleaned_files = clean_file_names(directory)
print("清理后的文件名：")
for name in cleaned_files:
    print(name)