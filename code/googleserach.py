from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

def google_search(query):
    driver = webdriver.Chrome()  # 确保已安装 ChromeDriver
    driver.get("https://www.google.com")

    # 输入查询
    search_box = driver.find_element("name", "q")
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)

    time.sleep(2)  # 等待页面加载

    # 获取搜索结果
    results = driver.find_elements("css selector", "div.tF2Cxc")
    for result in results:
        try:
            title = result.find_element("tag name", "h3").text
            link = result.find_element("css selector", "a").get_attribute("href")
            print(f"Title: {title}")
            print(f"Link: {link}")
        except:
            continue

    driver.quit()

google_search("site:assetstore.unity.com Zombie_Slayer")