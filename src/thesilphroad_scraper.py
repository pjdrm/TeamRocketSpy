'''
Created on Apr 10, 2018

@author: pjdrm
'''
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json

class TSRScraper():
    
    def __init__(self, out_file_path="./pokemon_moves.json"):
        self.out_file_path = out_file_path
        
    def scrape_traveller(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        chrome_driver = "./chromedriver"
        driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
        driver.get("https://sil.ph/ZeMota")
        avatar_type = driver.find_elements_by_xpath('//*[@id="leftPane"]/div[2]/h3[2]')[0].text
        name_on_tc = driver.find_elements_by_xpath('//*[@id="leftPane"]/div[2]/h3[3]')[0].text
        xp = driver.find_elements_by_xpath('//*[@id="leftPane"]/div[2]/h4[1]')[0].text
        team = driver.find_elements_by_xpath('//*[@id="leftPane"]/div[2]/h4[2]')[0].text
        trav_met = driver.find_elements_by_xpath('//*[@id="travelerCard"]/div[2]/div[3]/div[2]/div/h2')[0].text
        nest_reports = driver.find_elements_by_xpath('//*[@id="travelerCard"]/div[2]/div[4]/div[2]/span')[0].text
        pokedex = driver.find_elements_by_xpath('//*[@id="travelerCard"]/div[2]/div[9]/div[3]/p')[0].text
        play_style = driver.find_elements_by_xpath('//*[@id="travelerCard"]/div[2]/div[10]/div[1]/p/span[2]')[0].text
        lvl = driver.find_elements_by_xpath('//*[@id="avatarWrap"]/h2')[0].text
        city = driver.find_elements_by_xpath('//*[@id="leftPane"]/div[2]/h3[1]')[0].text
        we_badges = driver.find_elements_by_xpath('//*[@id="awards"]/div/img')
        basge_list_str = []
        for badge in we_badges:
            badge_str = badge.get_attribute('src')
            if badge_str.endswith("brown.png"):
                break
            basge_list_str.append(badge_str)
        print(avatar_type)
        print(name_on_tc)
        print(xp)
        print(team)
        print(trav_met)
        print(nest_reports)
        print(pokedex)
        print(play_style)
        print(lvl)
        print(city)
        print(basge_list_str)
        
        '''
        options = webdriver.FirefoxOptions()
        options.add_argument('-headless')
        driver = webdriver.Firefox(firefox_options=options, executable_path="./geckodriver")
        driver.get("https://sil.ph/ZeMota")
        driver.find_elements_by_xpath('//*[@id="travelerCardWrap"]/div')[0].screenshot("traveller_card.png")
        '''
        

tsr_scraper = TSRScraper()
tsr_scraper.scrape_traveller()