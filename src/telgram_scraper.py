'''
Created on Jun 15, 2018

@author: pjdrm
'''
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from datetime import datetime as dt
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver

TEST_RAID = 'Raid de <strong>Tyranitar</strong> às <strong>17:30</strong> em <span class="emoji  emoji-spritesheet-1" style="background-position: -216px -54px;" title="earth_americas">:earth_americas:</span><strong>Torre Divina Trindade</strong><br>Criada por <a href="#/im?p=%40vengefulshiro">@vengefulshiro</a> <em>(editada)</em> <em>(puxada)</em><br><span class="emoji  emoji-spritesheet-1" style="background-position: -378px -54px;" title="zap">:zap:</span>0 · <span class="emoji  emoji-spritesheet-1" style="background-position: -414px -54px;" title="snowflake">:snowflake:</span>4 · <span class="emoji  emoji-spritesheet-0" style="background-position: -162px -54px;" title="fire">:fire:</span>0 · <span class="emoji  emoji-spritesheet-4" style="background-position: -18px -72px;" title="question">:question:</span>1 · <span class="emoji  emoji-spritesheet-0" style="background-position: -234px -36px;" title="woman">:woman:</span><span class="emoji  emoji-spritesheet-0" style="background-position: -234px -36px;" title="woman">:woman:</span><span class="emoji  emoji-spritesheet-0" style="background-position: -198px -36px;" title="girl">:girl:</span><span class="emoji  emoji-spritesheet-0" style="background-position: -198px -36px;" title="girl">:girl:</span>5<br><span class="emoji  emoji-spritesheet-4" style="background-position: -558px -54px;" title="x">:x:</span> <span class="emoji  emoji-spritesheet-1" style="background-position: -378px -54px;" title="zap">:zap:</span>36 <a href="tg://resolve?domain=bela154" target="_blank" rel="noopener noreferrer">bela154</a><br><span class="emoji  emoji-spritesheet-4" style="background-position: -558px -36px;" title="white_check_mark">:white_check_mark:</span> <span class="emoji  emoji-spritesheet-1" style="background-position: -414px -54px;" title="snowflake">:snowflake:</span>40 <a href="tg://resolve?domain=CilioG0" target="_blank" rel="noopener noreferrer">CilioG0</a><span class="emoji  emoji-spritesheet-1" style="background-position: -54px -18px;" title="snail">:snail:</span><br><span class="emoji  emoji-spritesheet-4" style="background-position: -558px -36px;" title="white_check_mark">:white_check_mark:</span> <span class="emoji  emoji-spritesheet-1" style="background-position: -414px -54px;" title="snowflake">:snowflake:</span>28 <a href="tg://resolve?domain=Grand_Blaziken" target="_blank" rel="noopener noreferrer">GrandBlaziken</a><span class="emoji  emoji-spritesheet-1" style="background-position: -54px -18px;" title="snail">:snail:</span> +2<br><span class="emoji  emoji-spritesheet-4" style="background-position: -414px -90px;" title="black_small_square">:black_small_square:</span> <span class="emoji  emoji-spritesheet-4" style="background-position: -54px -90px;" title="heavy_minus_sign">:heavy_minus_sign:</span> - - <a href="tg://resolve?domain=vengefulshiro" target="_blank" rel="noopener noreferrer">@vengefulshiro</a>'

class TelgramScraper():
    
    def __init__(self, phone_code, phone_number, telgram_url="https://web.telegram.org/#/im"):
        self.sleep_time = 8
        self.driver = None
        self.telgram_url = telgram_url
        self.phone_code = phone_code
        self.phone_number = phone_number
        self.telgram_login()
    
    def create_driver_session(self, session_id, executor_url):
        # Save the original function, so we can revert our patch
        org_command_execute = RemoteWebDriver.execute
    
        def new_command_execute(self, command, params=None):
            if command == "newSession":
                # Mock the response
                return {'success': 0, 'value': None, 'sessionId': session_id}
            else:
                return org_command_execute(self, command, params)
    
        # Patch the function before creating the driver object
        RemoteWebDriver.execute = new_command_execute
    
        new_driver = webdriver.Remote(command_executor=executor_url, desired_capabilities={})
        new_driver.session_id = session_id
    
        # Replace the patched function with original function
        RemoteWebDriver.execute = org_command_execute
    
        return new_driver

    def telgram_login(self):
        chrome_options = Options()
        #chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        chrome_driver = "./chromedriver"
        self.driver = self.create_driver_session('3b545f830be5cc7da68db55c1cf39dbc', 'http://127.0.0.1:39203')#webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
        self.driver.get(self.telgram_url)
        time.sleep(self.sleep_time)
        phone_number_box = self.driver.find_elements_by_xpath('//*[@id="ng-app"]/body/div[1]/div/div[2]/div[2]/form/div[2]/div[2]/input')[0]
        phone_number_box.send_keys(self.phone_number)
        time.sleep(self.sleep_time)
        phone_code_box = self.driver.find_elements_by_xpath('//*[@id="ng-app"]/body/div[1]/div/div[2]/div[2]/form/div[2]/div[1]/input')[0]
        phone_code_box.clear()
        phone_code_box.send_keys(self.phone_code)
        next_button = self.driver.find_elements_by_xpath('//*[@id="ng-app"]/body/div[1]/div/div[2]/div[1]/div/a/my-i18n')[0]
        next_button.click()
        time.sleep(self.sleep_time)
        confirm_number_button = self.driver.find_elements_by_xpath('//*[@id="ng-app"]/body/div[5]/div[2]/div/div/div[2]/button[2]')[0]
        confirm_number_button.click()
        confirmation_code = input("Type the confirmation code:\n")
        confirmation_code_box = self.driver.find_elements_by_xpath('//*[@id="ng-app"]/body/div[1]/div/div[2]/div[2]/form/div[4]/input')[0]
        confirmation_code_box.clear()
        confirmation_code_box.send_keys(confirmation_code)
        time.sleep(self.sleep_time)
        
    def scrape_telgram(self):
        time_stamp = dt.now().strftime("%m-%d %H:%M")
        print("%s - New Telgram scrape"%time_stamp)
        raid_list = self.get_raids(self.driver)
        print("Done Telgram Scraping")
        return raid_list
        
    def get_raids(self, driver):
        raids_expo = self.driver.find_element_by_xpath('//*[@id="ng-app"]/body/div[1]/div[2]/div/div[1]/div[2]/div/div[1]//*[text()="Raids PoGo Expo"]')
        raids_expo.click()
        raid_list = []
        all_chats = driver.find_elements_by_xpath('//*[@class="im_message_text"]')
        for chat in all_chats.reverse():
            message = chat.get_attribute("innerHTML")
            print(message)
            if message.startswith("Raid de <strong>"):
                print("Telgram raid shout: %s" % message)
                raid_info = self.parse_telgram_raid_shout(message)
                raid_list.append(raid_info)
        return raid_list
        #return [self.parse_telgram_raid_shout(TEST_RAID)]
    
    def parse_telgram_raid_shout(self, raid_shout):
        boss = None
        level = None
        raid_starts_in = None
        raid_ends_in = None
        boss_desc = raid_shout.split("Raid de <strong>")[1].split("</strong>")[0]
        if boss_desc.startswith("nível"):
            level = boss_desc.split("nível ")[1]
            hatched = False
            raid_starts_in = raid_shout.split("<em>(puxada)</em><br><em>Aberto entre ")[1].split(" ")[0]
        else:
            hatched = True
            boss = boss_desc
            if "<em>Aberto entre " in raid_shout:
                raid_ends_in = raid_shout.split("<em>Aberto entre ")[1].split("</em><br>")[0].split(" e ")[1]
            
        gym_separator = None
        if "earth_americas" in raid_shout:
            gym_separator = ":earth_americas:</span><strong>"
        else:
            gym_separator = 'title="star2">:star2:</span><strong>'
        gym_name = raid_shout.split(gym_separator)[1].split("</strong><br>")[0]
        raid_dict = {'level': level, 
                     'boss': boss, 
                     'raid_starts_in': raid_starts_in,
                     'raid_ends_in': raid_ends_in,
                     'gym_name': gym_name,
                     'hatched': hatched}
        return raid_dict
        
        
        
#tg_scraper = TelgramScraper("+1", "3139854603")
#tg_scraper.scrape_telgram()
#print(tg_scraper.parse_telgram_raid_shout())