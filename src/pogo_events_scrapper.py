'''
Created on Nov 24, 2018

@author: ZeMota
'''
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime

class PogoEventsScrapper():
    
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument("user-agent=WIP")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('disable-infobars')
        chrome_options.add_argument('--disable-extensions')
        
        chrome_driver = "./chromedriver"
        self.driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
        
    def scrape_pogo_events(self):
        self.driver.get('https://p337.info/pokemongo/')
        pogo_event_list = []
        for i in range(1, 10):
            event_icon = self.driver.find_elements_by_xpath('//*[@id="container_right"]/a['+str(i)+']/div/div[@class="extra_timer_left"]/img')
            if len(event_icon) == 0:
                break
            event_icon = event_icon[0].get_attribute("src")
            event_desc = self.driver.find_elements_by_xpath('//*[@id="container_right"]/a['+str(i)+']/div/div[@class="extra_timer_right"]')[0].text
            split_str = event_desc.split("\n")
            if len(split_str) == 3:
                date_split = split_str[2].split(" ")
            else:
                date_split = split_str[1].split(" ")
            date = date_split[0]+" "+date_split[1]+" "+date_split[4]
            event_end_date = datetime.strptime(date[4:], '%d-%b-%Y (%H:%M)')
            present = datetime.now()
            if event_end_date < present:
                continue #Event is over
                
            if ("Starts" in event_desc) or ("Start" in event_desc):
                desc = split_str[0].replace(" Starts", "").replace(" Start", "")
                date = "Starts: "+date
            else:
                desc = split_str[0].replace(" Ends", "").replace(" End", "")
                date = "Ends: "+date
            pogo_event_list.append({"icon": event_icon, "desc": desc, "date": date})
        return pogo_event_list
            
#PogoEventsScrapper()