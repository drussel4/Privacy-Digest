import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By

# Align driver and set options
options = webdriver.ChromeOptions()
# options.add_argument('--headless=new')
# options.add_argument('--start-maximized')
# options.add_argument('--no-sandbox')
# options.add_argument('--disable-dev-shm-usage')
# user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
# options.add_argument(f'user-agent={user_agent}')
if os.environ.get('CI', False):
    print('On GH, installing driver from environ')
    driver_path = os.environ['CHROMEWEBDRIVER'] + '/chromedriver'
    chrome_service = ChromeService(driver_path)
    driver = webdriver.Chrome(service=chrome_service, options=options)
else:
    print('Local, installing driver based on version number')
    chrome_version = '117.0.5938.92'
    chrome_service = ChromeService(version=chrome_version)
    driver = webdriver.Chrome(service=chrome_service, options=options)
print('driver:', driver)

d = driver.__dict__
for k in d.keys():
    if k == 'caps':
        dd = d[k]
        for kk in dd.keys():
            if kk == 'browserVersion':
                print('browserVersion:', dd[kk])

def scrape():
    
    print('Beginning scrape()')
    
    # Testing sites
    sites = [
        ('MusicLeague', 'https://musicleague.com/privacy'),
        ('Spotify', 'https://www.spotify.com/us/legal/privacy-policy/'),
        ('Apple Music', 'https://www.apple.com/legal/privacy/data/en/apple-music/'),
    ]
    for site in sites:
        
        driver.get(site[1])
        time.sleep(1)
        
        # Retrieve whole body text
        body_text = driver.find_element(By.XPATH, "/html/body").text
        
        with open('{}.json'.format(site[0]), 'w') as fp:
            json.dump(body_text, fp, default=str)
            
        time.sleep(1)
    
    # Closing the driver
    driver.close()
    
    return None

scrape()
