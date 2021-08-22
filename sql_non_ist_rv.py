import pyodbc
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
import os

GROUP_NUMBER = os.getenv('GROUP_NUMBER')
GROUP_ID = os.getenv('GROUP_ID')
server = os.getenv('SERVER')
database = os.getenv('DATABASE') 
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')

def init_webdriver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("window-size=5760,3240")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument('--disable-gpu')
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def get_stores(latitude, longitude, driver):
    start = time.time()
    url = f"https://www.google.com/maps/search/{latitude}+{longitude}"
    driver.get(url)
    time.sleep(0.1)
    try:
        driver.find_element_by_xpath("//button[@aria-label='Agree to the use of cookies and other data for the purposes described']").click()
    except:
        pass
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, '//span[@class="widget-pane-link"]')))
    print(f"Elapsed Time: {int(time.time() - start)} seconds")
    
    return driver.find_element_by_xpath('//span[@class="widget-pane-link"]').text


driver = init_webdriver()
cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
cursor = cnxn.cursor()

stale_element_count = 0
while True:
    try:
        cursor.execute(f'SELECT * FROM stores WHERE [Checked] IS NULL AND ID % {GROUP_NUMBER} = {GROUP_ID}')
        row = cursor.fetchone()
        if not row:
            print('List is finished')
            break
        name, lat, lon, city, town, checked, ID = row
        print('Row: ', row,'Stale element count: ', stale_element_count)
        addr = get_stores(lat, lon, driver)
        cursor.execute("insert into store_address values (?,?,?,?,?,?,?,?)",name, lat, lon, city,town, '1', ID, addr)
        cursor.execute(fr"UPDATE stores set Checked = 1 WHERE ID = {ID}")
        cnxn.commit()
    
    except StaleElementReferenceException:
        stale_element_count += 1

        

