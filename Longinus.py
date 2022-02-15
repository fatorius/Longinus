from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

options = webdriver.ChromeOptions()
options.add_argument("--headless")

driver = Service(ChromeDriverManager().install())
browser = webdriver.Chrome(service=driver, options=options)

browser.get('https://www.hugosouza.com')

print(browser.page_source)