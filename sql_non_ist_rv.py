import pyodbc
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import os



server = 'tcp:berkayserver.database.windows.net' 
database = 'scraper_db' 
username = 'scr_v' 
password = 'Vestel54'


def init_webdriver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("window-size=5760,3240")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument('--disable-gpu')
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    #chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def get_stores(latitude, longitude, driver):
    start = time.time()
    url = f"https://www.google.com/maps/search/{latitude}+{longitude}"
    driver.get(url)
    time.sleep(1)
    try:
        driver.find_element_by_xpath("//button[@aria-label='Agree to the use of cookies and other data for the purposes described']").click()
    except:
        pass
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//span[@class="widget-pane-link"]')))
    print(f"Elapsed Time: {int(time.time() - start)} seconds")
    
    return driver.find_element_by_xpath('//span[@class="widget-pane-link"]').text


driver = init_webdriver()
cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
cursor = cnxn.cursor()

cursor.execute('SELECT COUNT(*) FROM stores')
total_store_counts = cursor.fetchall()[0][0]
ind = total_store_counts
latest_index = 30000
while ind > latest_index:
    cursor.execute(f'SELECT * FROM stores WHERE Store_id = {ind-1}')
    row = cursor.fetchall()[0]
    st_id, name, lat, lon, city, town = row
    addr = get_stores(lat, lon, driver)
    cursor.execute(f"insert into store_address values ('{name}','{lat}','{lon}','{city}','{town}','{addr}')")
    cnxn.commit()
    print('Index: ', ind)
    ind -= 1



#data = pd.read_sql("SELECT TOP(1000) * FROM dbo.store_address", cnxn)
#print(data.head())
# Do the insert

