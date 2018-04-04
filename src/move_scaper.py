'''
Created on Apr 3, 2018

@author: pjdrm
'''
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json

class MoveScraper():
    
    def __init__(self, out_file_path="./pokemon_moves.json"):
        self.out_file_path = out_file_path
        
    def scrape_moves(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument("user-agent=WIP")
        chrome_driver = "./chromedriver"
        driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
        driver.get("https://pokemon.gameinfo.io/en/moves")
        moves = driver.find_elements_by_xpath('//*[@id="content"]/section/div[2]/article[1]/table/tbody/tr')
        move_types = driver.find_elements_by_xpath('//*[@id="content"]/section/div[2]/article[1]/table/tbody/tr/td[2]/a/span')
        move_dict = {}
        for move, type in zip(moves, move_types):
            move = move.text.split("   ")[1].split(" ")
            if len(move) == 4:
                move = move[0] + " " + move[1]
            else:
                move = move[0]
            type = type.get_attribute('class').split("-")[3].split(" ")[0]
            move_dict[move] = type
            print("%s %s" % (type, move))
            
        moves = driver.find_elements_by_xpath('//*[@id="content"]/section/div[2]/article[2]/table/tbody/tr')
        move_types = driver.find_elements_by_xpath('//*[@id="content"]/section/div[2]/article[2]/table/tbody/tr/td[2]/a/span')
        for move, type in zip(moves, move_types):
            move = move.text.split("   ")[1].split(" ")
            if len(move) == 4:
                move = move[0] + " " + move[1]
            else:
                move = move[0]
            type = type.get_attribute('class').split("-")[3].split(" ")[0]
            move_dict[move] = type
            print("%s %s" % (type, move))
        with open(self.out_file_path, 'w+') as fp:
            json.dump(move_dict, fp, indent=4)
        
move_scraper = MoveScraper()
move_scraper.scrape_moves()