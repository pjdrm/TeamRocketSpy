'''
Created on Nov 23, 2018

@author: pjdrm
'''
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class PoGoEventsBot():
    
    def __init__(self):
        self.pogo_events_url = 'https://p337.info/pokemongo/'
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument("user-agent=WIP")
        
        chrome_driver = "./chromedriver"
        self.driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
        self.scrape_pogo_events()
        
    def scrape_pogo_events(self):
        self.driver.get(self.pogo_events_url)
        events = self.driver.find_elements_by_xpath('//*[@id="container_right"]/a/div')
        for i in range(1,10):
            event_icon = self.driver.find_elements_by_xpath('//*[@id="container_right"]/a['+str(i)+']/div/div[1]/img')
            if len(event_icon) == 0:
                break
            event_icon = event_icon[0].get_attribute("src")
            event_dsc = self.driver.find_elements_by_xpath('//*[@id="container_right"]/a['+str(i)+']/div/div[2]')[0].text
            print("Icon: %s Event desc: %s"%(event_icon, event_dsc))
            
PoGoEventsBot()