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

### USE below code when running the script locally, left commented otherwise

# from dotenv import load_dotenv
# load_dotenv()
# username = os.getenv('DB_USERNAME')
# password = os.getenv('DB_PASSWORD')

###

# total number of scripts that will run concurrently
GROUP_NUMBER = os.getenv('GROUP_NUMBER') 
# specific group ID for the associated script
GROUP_ID = os.getenv('GROUP_ID') 

# connections parameters that will be used in the scripts / the variables will be set through Heroku's 'Config Vars' section
server = os.getenv('SERVER')
database = os.getenv('DATABASE')
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')
print('GROUP_ID: ', GROUP_ID, 'GROUP_NUMBER: ', GROUP_NUMBER, 'USERNAME: ',username )

def init_webdriver():
    '''Initiates the Chrome driver with pre-defined options and returns driver object'''

    # Below options allow to initiate driver without starting a browser screen (necessary for Heroku)
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
    '''Navigates to the google maps page and make a single query with the given coordinates and returns the text value of the address field'''

    # Starting time to calculate elapsing time in each iteration
    start = time.time()
    
    # Creating the url string and directing the driver to the gmaps page 
    url = f"https://www.google.com/maps/search/{latitude}+{longitude}"
    driver.get(url)
    
    # Let the script stop for 0.1 seconds just to be safe for interacting with the page
    #time.sleep(0.1)
    load_time = int(time.time() - start)

    # Webdriver expression to wait precisely until the Address field becomes visible
    address_text_xpath = '//div[@data-tooltip="Copy address"]//*[string-length(text()) > 2]'
    WebDriverWait(driver, 6).until(EC.text_to_be_present_in_element((By.XPATH, address_text_xpath),''))
    
    time.sleep(9)
    address_text = driver.find_element_by_xpath('//span[@class="widget-pane-link"]').text
    
    # Gather the web element object with the corresponding information and get the text value of the object
    #address_text = driver.find_element_by_xpath(address_text_xpath).text

    # Subtract the current time from the starting time value to obtain total seconds passed
    print(f"Load time: {load_time} --- Elapsed Time: {int(time.time() - start)} seconds --- ADR: {address_text}")

    return address_text

# Start webdriver
driver = init_webdriver()

# Connect to the SQL Database with the given credentials
cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + server + ';DATABASE=' + database +';UID=' + username + ';PWD=' + password)

# Create a cursor object to interact with the SQL server
cursor = cnxn.cursor()

def main(cursor=cursor):
    '''
    Employes all of the required functions and variables to loop through the list of stores that will be scraped on Google Maps. 
    Queries the stores within the scope of the script that have not been scraped yet:

    - Fetches one, 
    - Feeds the row values into 'get_stores' func,
    - Executes a SQL query command to insert the row with the address value added (e.g., StoreID, Store_Name, City, Address...)
    - Changes 'Checked' column as '1' of the corresponding store in the source table 

    '''
    
    
    driver.get('https://www.google.com/maps/search/homegoods+stores+in+fatih+istanbul')
    time.sleep(5)
    try:
        driver.find_element_by_xpath("//*[contains(text(),'I agree')]").click()
        time.sleep(5)
    except:
        print('I agree click error')

    # Number of Stale Element errors occured 
    stale_element_count = 0

    # Number of Timeout Exception errors occured
    timeout_count = 0

    # Loops until no stores to be scraped, left
    while True:

        try:
            # SELECTs all stores whose 'Checked' column is NULL and whose 'GROUP_ID' value equals to the mod division of ID number to GROUP_NUMBER value
            # so that when the script is distributed into 5 platforms, these scripts will not step in each other's chunk of stores  
            cursor.execute(f'SELECT * FROM hgoods_raw WHERE [checked] IS NULL AND ID % {GROUP_NUMBER} = {GROUP_ID}')

            # Gets one store in the queried list of stores    
            row = cursor.fetchone()

            # If the script ran out of available stores to be scraped it will break the loop
            if not row:
                print('List finished')
                break

            # Unpacks row into variables
            name, href ,lat, lon, ID, checked = row
            
            # Prints the values
            print('Row: ', name, 'Stale element count: ', stale_element_count, 'Timeout count: ', timeout_count)

            # Gets the address of the store
            addr = get_stores(lat, lon, driver)

            # Inserts the row with the address value into the store_address table in the database
            cursor.execute("insert into store_address values (?,?,?,?,?,?,?)", name, href, lat, lon, ID, '1',addr)

            # Updates the corresponding store record in the source table to emhasize that the store has been scraped now
            cursor.execute(fr"UPDATE hgoods_raw set checked = 1 WHERE ID = {ID}")

            # Commit the changes made in the SQL Server
            cnxn.commit()


        # Keeps track of Stale Element errors
        except StaleElementReferenceException:
            stale_element_count += 1
        
        # Keeps track of Timeout errors
        except  TimeoutException:
            timeout_count += 1



# As a best practice use 'if __name__' expression before calling the main function
if __name__ == '__main__':
    main()

