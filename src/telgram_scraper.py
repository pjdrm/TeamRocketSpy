'''
Created on Jun 15, 2018

@author: pjdrm
'''
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import threading
from datetime import datetime as dt, timedelta
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver

TEST_RAID = 'Raid de <strong>nível 5</strong> às <strong>14:50</strong> em <span class="emoji  emoji-spritesheet-0" style="background-position: -198px -54px;" title="star2">:star2:</span><strong>Big Pet</strong><br>Criada por <a href="tg://resolve?domain=AlchemistCook" target="_blank" rel="noopener noreferrer">AlchemistCook</a>  <em>(puxada)</em><br><em>Aberto entre 14:55 e 15:40</em><br><span class="emoji  emoji-spritesheet-1" style="background-position: -378px -54px;" title="zap">:zap:</span>1 · <span class="emoji  emoji-spritesheet-1" style="background-position: -414px -54px;" title="snowflake">:snowflake:</span>0 · <span class="emoji  emoji-spritesheet-0" style="background-position: -162px -54px;" title="fire">:fire:</span>0 · <span class="emoji  emoji-spritesheet-0" style="background-position: -234px -36px;" title="woman">:woman:</span><span class="emoji  emoji-spritesheet-0" style="background-position: -234px -36px;" title="woman">:woman:</span><span class="emoji  emoji-spritesheet-0" style="background-position: -198px -36px;" title="girl">:girl:</span><span class="emoji  emoji-spritesheet-0" style="background-position: -198px -36px;" title="girl">:girl:</span>1<br><span class="emoji  emoji-spritesheet-4" style="background-position: -414px -90px;" title="black_small_square">:black_small_square:</span> <span class="emoji  emoji-spritesheet-1" style="background-position: -378px -54px;" title="zap">:zap:</span>35 <a href="tg://resolve?domain=AlchemistCook" target="_blank" rel="noopener noreferrer">AlchemistCook</a>'
RAID_UNORGANIZED_SEP = "Abre uma raid de <strong>"
RAID_ORGANIZED_SEP = "Raid de <strong>"
TELGRAM_GROUPS = ["Raids PoGo Expo", "Raids PoGo Areeiro", "Raids PoGo Avenida/Baixa"]

class TelgramScraper():
    
    def __init__(self, phone_code,
                 phone_number,
                 telgram_groups,
                 telgram_url="https://web.telegram.org/#/login",
                 restore_session=True,
                 log_in=False,
                 session_info_file="chrome_session_info.txt",
                 raids_scraped_file="raids_list.txt"):
        self.sleep_time = 8
        self.driver = None
        self.telgram_url = telgram_url
        self.phone_code = phone_code
        self.phone_number = phone_number
        self.raids_scraped_file = raids_scraped_file
        self.telgram_groups = telgram_groups
        self.session_info_file = session_info_file
        if not restore_session:
            self.init_driver()
        else:
            self.restore_session()
            
        if log_in:
            self.telgram_login()
    
    def init_driver(self):
        chrome_options = Options()
        #chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        chrome_driver = "./chromedriver"
        self.driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
        self.driver.get(self.telgram_url)
        time.sleep(self.sleep_time)
        
    def restore_session(self):
        with open(self.session_info_file) as f:
            lins = f.readlines()
        session_id = lins[0][:-1]
        executor_url = lins[1]
        self.driver = self.create_driver_session(session_id, executor_url)
    
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
        #RemoteWebDriver.execute = new_command_execute
    
        new_driver = webdriver.Remote(command_executor=executor_url, desired_capabilities={})
        new_driver.session_id = session_id
    
        # Replace the patched function with original function
        RemoteWebDriver.execute = org_command_execute
    
        return new_driver

    def telgram_login(self):
        phone_number_box = self.driver.find_elements_by_xpath('//*[@id="ng-app"]/body/div[1]/div/div[2]/div[2]/form/div[2]/div[2]/input')[0]
        phone_number_box.send_keys(self.phone_number)
        time.sleep(self.sleep_time)
        phone_code_box = self.driver.find_elements_by_xpath('//*[@id="ng-app"]/body/div[1]/div/div[2]/div[2]/form/div[2]/div[1]/input')[0]
        phone_code_box.clear()
        phone_code_box.send_keys(self.phone_code)
        time.sleep(self.sleep_time)
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
        
    def is_present_raid(self, raid_info):
        raid_end_time = None
        if raid_info["raid_starts_in"] is not None:
            raid_end_time = raid_info["raid_starts_in"]
            raid_time_obj = dt.strptime(raid_end_time, '%H:%M')
            raid_dur = timedelta(minutes=45)
            raid_time_obj = raid_time_obj + raid_dur
            raid_end_time = raid_time_obj.strftime("%H:%M")
        elif raid_info["raid_ends_in"] is not None:
            raid_end_time = raid_info["raid_ends_in"]
        else:
            return None #TODO: handle only having meet time case
        
        time_stamp_obj = dt.now()
        time_stamp = time_stamp_obj.strftime("%H:%M").split(":")
        hour = int(time_stamp[0])
        min = int(time_stamp[1])
        
        raid_end_time_obj = dt.strptime(raid_end_time, '%H:%M')
        raid_end_time = raid_end_time.split(":")
        raid_hour = int(raid_end_time[0])
        raid_min = int(raid_end_time[1])
        
        time_diff = raid_end_time_obj-time_stamp_obj
        time_diff = time_diff.seconds/60
        if time_diff >= 100:
            #Case where currently there are no active raids
            return False
        
        if raid_hour < hour:
            return False
        elif raid_hour == hour:
            if raid_min > min:
                return True
            else:
                return False
        else:
            return True
    
    def check_is_raid_shout(self, message):
        is_raid_shout = False
        raid_boss_sep = None
        if message.startswith("Raid de <strong>"):
                raid_boss_sep = RAID_ORGANIZED_SEP
                is_raid_shout = True
        elif ":loudspeaker:</span> Abre uma" in message:
            raid_boss_sep = RAID_UNORGANIZED_SEP
            is_raid_shout = True
        return is_raid_shout, raid_boss_sep
    
    def scrape_telgram(self):
        threading.Timer(240, self.scrape_telgram).start()
        raid_list = []
        for telgram_group in self.telgram_groups:
            time_stamp = dt.now().strftime("%m-%d %H:%M")
            print("%s - New %s scrape"%(time_stamp, telgram_group))
            raids_expo = self.driver.find_element_by_xpath('//*[@id="ng-app"]/body/div[1]/div[2]/div/div[1]/div[2]/div/div[1]//*[text()="'+telgram_group+'"]')
            raids_expo.click()
            time.sleep(self.sleep_time)
            all_chats = self.driver.find_elements_by_xpath('//*[@class="im_history_messages_peer"]//*[@class="im_message_text"]')
            all_chats.reverse()
            for chat in all_chats:
                message = chat.get_attribute("innerHTML")
                is_shout, raid_boss_sep = self.check_is_raid_shout(message)
                #print(message)
                if is_shout:
                    print("Telgram raid shout: %s" % message)
                    raid_info = self.parse_telgram_raid_shout(message, raid_boss_sep)
                    active_flag = self.is_present_raid(raid_info)
                    if active_flag is None: #Means we dont know end time
                        continue
                    elif not active_flag:
                        break
                    print("Parsed raid shout: %s" % raid_info)
                    raid_list.append(raid_info)
            print("Done Scraping "+telgram_group)
        with open(self.raids_scraped_file, "w+") as raids_f:
            raids_f.write(str(raid_list))
        #return raid_list
        '''
        raid_info = self.parse_telgram_raid_shout(TEST_RAID, RAID_UNORGANIZED_SEP)
        active_flag = self.is_present_raid(raid_info)
        return [raid_info]
        '''
    
    def parse_telgram_raid_shout(self, raid_shout, raid_boss_sep):
        boss = None
        level = None
        raid_starts_in = None
        raid_ends_in = None
        
        boss_desc = raid_shout.split(raid_boss_sep)[1].split("</strong>")[0]
        if boss_desc.startswith("nível"):
            level = boss_desc.split("nível ")[1]
            hatched = False
        else:
            hatched = True
            boss = boss_desc
            
        if "<em>Aberto entre " in raid_shout:
            raid_starts_in = raid_shout.split("<em>Aberto entre ")[1].split(" ")[0]
            raid_ends_in = raid_shout.split("<em>Aberto entre ")[1].split("</em><br>")[0].split(" e ")[1]
        elif "entre as <strong>" in raid_shout:
            raid_starts_in = raid_shout.split("entre as <strong>")[1].split("</strong>")[0]
            raid_ends_in = raid_shout.split(" e as <strong>")[1].split("</strong>")[0]
        
        gym_separator = None
        if "earth_americas" in raid_shout:
            gym_separator = ":earth_americas:</span><strong>"
        elif ":star2:" in raid_shout:
            gym_separator = ':star2:</span><strong>'
        elif ":deciduous_tree:" in raid_shout:
            gym_separator = ":deciduous_tree:</span><strong>"
        else:
            gym_separator = ":question:</span><strong>"
        gym_name = raid_shout.split(gym_separator)[1].split("</strong><br>")[0]
        raid_dict = {'level': level, 
                     'boss': boss, 
                     'raid_starts_in': raid_starts_in,
                     'raid_ends_in': raid_ends_in,
                     'gym_name': gym_name,
                     'hatched': hatched}
        return raid_dict        
        
tg_scraper = TelgramScraper("+1", "3139854603", TELGRAM_GROUPS)
tg_scraper.scrape_telgram()
#tg_scraper.scrape_telgram()
#print(tg_scraper.parse_telgram_raid_shout())