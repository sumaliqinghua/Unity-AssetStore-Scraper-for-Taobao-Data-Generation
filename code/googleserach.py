import site
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

def google_search(query):
    driver = webdriver.Chrome()  # 确保已安装 ChromeDriver
    try:
        driver.get("https://www.google.com")

        # 输入查询
        search_box = driver.find_element("name", "q")
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)

        time.sleep(2)  # 等待页面加载

        # 获取第一个搜索结果
        results = driver.find_elements("css selector", "div.tF2Cxc")
        if results:
            try:
                first_result = results[0]
                title = first_result.find_element("tag name", "h3").text
                link = first_result.find_element("css selector", "a").get_attribute("href")
                return {'title': title, 'link': link}
            except:
                return None
        return None
    finally:
        driver.quit()

if __name__ == "__main__":
    # 测试搜索功能
    test_query = "site:assetstore.unity.com Unity Asset"
    print(f"测试搜索: {test_query}")
    result = google_search(test_query)
    if result:
        print(f"Title: {result['title']}")
        print(f"Link: {result['link']}")
    else:
        print("No results found")