import threading
import msvcrt
import time

def select_with_timeout(prompt, default, timeout=8):
    """
    带超时的用户输入选择
    :param prompt: 提示信息
    :param default: 默认值
    :param timeout: 超时时间（秒）
    :return: 用户输入或默认值
    """
    print(f"{prompt} (默认: {default}, {timeout}秒后自动选择默认值)")
    
    result = [default]
    input_thread = threading.Thread(target=lambda: get_input(result))
    input_thread.daemon = True
    input_thread.start()
    input_thread.join(timeout)
    
    if input_thread.is_alive():
        # 清除输入缓冲区
        while msvcrt.kbhit():
            msvcrt.getch()
        print(f"\n已超时，使用默认值: {default}")
        return default
    
    return result[0]

def get_input(result):
    """
    获取用户输入的辅助函数
    :param result: 存储用户输入的列表
    """
    user_input = input().strip()
    result[0] = user_input if user_input else result[0]
