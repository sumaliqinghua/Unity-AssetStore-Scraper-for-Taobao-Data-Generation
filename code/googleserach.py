import site
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

def google_search(query):
    # 配置Chrome选项
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--proxy-server=http://127.0.0.1:2612')  # 添加代理设置
    
    driver = webdriver.Chrome(options=chrome_options)  # 确保已安装 ChromeDriver
    try:
        # 打开Google并执行初始搜索
        driver.get("https://www.google.com")
        search_box = driver.find_element("name", "q")
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        time.sleep(2)  # 等待页面加载

        while True:
            # 获取当前页面的搜索结果
            results = driver.find_elements("css selector", "div.tF2Cxc")
            search_results = []
            
            for result in results[:5]:  # 限制为前5个结果
                try:
                    title = result.find_element("tag name", "h3").text
                    link = result.find_element("css selector", "a").get_attribute("href")
                    search_results.append({'title': title, 'link': link})
                except:
                    continue

            # 显示当前搜索结果
            if search_results:
                print("\n当前页面的搜索结果：")
                for i, result in enumerate(search_results, 1):
                    print(f"{i}. 标题: {result['title']}")
                    print(f"   链接: {result['link']}\n")
            else:
                print("\n当前页面未找到搜索结果")

            # 询问是否使用当前页面的结果
            user_input = input("\n是否使用当前页面的结果？(y/n): ").strip().lower()
            if user_input == 'y':
                return search_results
            elif user_input == 'n':
                print("\n请在浏览器中修改搜索内容，修改完成后回车继续...")
                input()
                time.sleep(2)  # 等待可能的页面加载
                continue
            else:
                print("无效的输入，请重试")
                
    finally:
        # 询问是否关闭浏览器
        close = input("\n是否关闭浏览器？(y/n): ").strip().lower()
        if close == 'y':
            driver.quit()
        else:
            print("浏览器将保持打开状态，请手动关闭。")
            return None  # 如果保持浏览器打开，返回None表示需要重新开始搜索流程

if __name__ == "__main__":
    # 测试搜索功能
    test_query = "site:assetstore.unity.com Unity Asset"
    print(f"测试搜索: {test_query}")
    results = google_search(test_query)
    if results:
        for i, result in enumerate(results, 1):
            print(f"\n结果 {i}:")
            print(f"Title: {result['title']}")
            print(f"Link: {result['link']}")
    else:
        print("No results found")