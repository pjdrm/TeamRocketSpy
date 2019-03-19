'''
Created on Nov 24, 2018

@author: ZeMota
'''
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import sys
import json

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
        event_links = []
        for event_el in self.driver.find_elements_by_xpath('//*[@id="container_right"]/a'):
            event_link = event_el.get_attribute("href")
            if event_link == "https://p337.info/pokemongo/countdowns/community-day.php":
                break
            event_links.append(event_link)
                
        for event_link in event_links:
            self.driver.get(event_link)
            event_desc = self.driver.find_elements_by_xpath('//*[@class="clock_contain mas"]')[0].get_attribute("innerText")
            if ("Your Local Time:" not in event_desc) or ("have Ended" in event_desc) or ("has Ended" in event_desc):
                continue
            split_str = event_desc.split("Your Local Time:")
            date = split_str[1].strip()
            date_split = date.split(" ")
            date = date_split[0]+" "+date_split[1]+" "+date_split[4]
            
            if "Europe" in split_str[0]:
                event_name = split_str[0].strip().replace("Europe ", "").replace("starts", "Starts")
            else:
                event_name = split_str[0].split("\n")[0]
            if ("Start" in event_name):
                desc = event_name.replace(" Starts", "").replace(" Start", "")
                date = "Starts: "+date
            else:
                desc = event_name.replace(" Ends", "").replace(" End", "")
                date_obj = datetime.strptime(date.split(" ")[1], "%d-%b-%Y")
                if date_obj < datetime.now():
                    date = "Is over"
                else:
                    date = "Ends: "+date
            desc = desc.replace(" in", "")
            pogo_event_list.append({"desc": desc, "date": date})
        return pogo_event_list

if __name__ == "__main__":
    tr_spy_config_path = "./config/tr_spy_config.json"
    if len(sys.argv) == 2:
        tr_spy_config_path = sys.argv[1]
    
    with open(tr_spy_config_path) as data_file:    
        tr_spy_config = json.load(data_file)
        
    pogo_events_out = tr_spy_config["pogo_events"]
    pogo_event_list = PogoEventsScrapper().scrape_pogo_events()
    with open(pogo_events_out, "w+") as f:
        f.write(str(pogo_event_list))
        
#PogoEventsScrapper().scrape_pogo_events()