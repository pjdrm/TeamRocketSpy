'''
Created on Jun 15, 2018

@author: pjdrm
'''
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import pickle

class TelgramScraper():
    
    def __init__(self, phone_code, phone_number, telgram_url="https://web.telegram.org/#/im"):
        self.telgram_url = telgram_url
        self.phone_code = phone_code
        self.phone_number = phone_number
        
    def scrape_telgram(self):
        chrome_options = Options()
        #chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        chrome_driver = "./chromedriver"
        driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
        for cookie in pickle.load(open("ChromeCookies.pkl", "rb")):
            driver.add_cookie(cookie)
        driver.get(self.telgram_url)
        time.sleep(1)
        phone_number_box = driver.find_elements_by_xpath('//*[@id="ng-app"]/body/div[1]/div/div[2]/div[2]/form/div[2]/div[2]/input')[0]
        phone_number_box.send_keys(self.phone_number)
        time.sleep(1)
        phone_code_box = driver.find_elements_by_xpath('//*[@id="ng-app"]/body/div[1]/div/div[2]/div[2]/form/div[2]/div[1]/input')[0]
        phone_code_box.clear()
        phone_code_box.send_keys(self.phone_code)
        next_button = driver.find_elements_by_xpath('//*[@id="ng-app"]/body/div[1]/div/div[2]/div[1]/div/a/my-i18n')[0]
        next_button.click()
        raids_expo = driver.find_element_by_xpath('//*[@id="ng-app"]/body/div[1]/div[2]/div/div[1]/div[2]/div/div[1]/ul/li[1]/a')
        raids_expo.click()
        self.get_raids(driver)
        #phone_correct_button = driver.find_elements_by_xpath('//*[@id="ng-app"]/body/div[6]/div[2]/div/div/div[2]/button[2]')[0]
        #phone_correct_button.click()
        print("Done Telgram Scraping")
        #pickle.dump(driver.get_cookies() , open("ChromeCookies.pkl","wb"))
        
    def get_raids(self, driver):
        all_chats = driver.find_elements_by_xpath('//*[@class="im_message_text"]')
        for chat in all_chats:
            message = chat.get_attribute("innerHTML")
            if message.startswith("Raid de <strong>"):
                print(message)
        
tg_scraper = TelgramScraper("+1", "3139854603")
tg_scraper.scrape_telgram()