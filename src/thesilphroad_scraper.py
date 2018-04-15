'''
Created on Apr 10, 2018

@author: pjdrm
'''
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import urllib.request
import discord
from discord.ext import commands

class TSRScraper():
    
    def __init__(self, traveler_card_db="/home/pjdrm/Desktop/traveler_cards_db.json"):
        self.server_emojis = json.load(open("../server-emojis.json"))
        self.traveler_card_db = traveler_card_db
        self.bot_token = "NDIyODM5NTgzODc3NjI3OTA1.DYhnlA.Ax_cAy7J4KoPHbD-vjApwC_4l6c"
        self.test_card = json.load(open(traveler_card_db))
        self.bot = commands.Bot(command_prefix="$", description='TSRBot')
    
    def get_traveler_card_embeded(self, traveler_card):
        nick_name = [*traveler_card][0]
        traveler_info = traveler_card[nick_name]
        desc = "Lvl: "+traveler_info["lvl"]+"\n"+\
               "XP: "+traveler_info["xp"]+"\n"+\
               "Team: "+traveler_info["team"].title()+"\n"+\
               "Handshakes: "+traveler_info["trav_met"]+"\n"+\
               "Nest Reports: "+traveler_info["nest_reports"]+"\n"+\
               "Joined: "+traveler_info["joined"]+"\n"+\
               "Raids: "+traveler_info["raids"]+"\n"+\
               "Pokedex: "+traveler_info["pokedex"]+"\n"
        badge_emoji = ""
        for badge_sr in traveler_info["badges"]:
            badge_emoji += self.server_emojis[badge_sr]
        desc += "Badges: " + badge_emoji
        
        playstyle_desc = traveler_info["play_style"]+"\nAcitve around "+traveler_info["city"]
        tc_embed=discord.Embed(title="Playstyle", description=playstyle_desc, color=0x399f21)
        author = traveler_info["avatar_type"]+" "+nick_name
        author_url =  "https://sil.ph/" + nick_name
        tc_embed.set_author(name=author, url=author_url)
        tc_embed.add_field(name="Game Stats", value=desc)
        tc_embed.set_thumbnail(url=traveler_info["avatar_image_file"])
        return tc_embed
        
    def scrape_traveler(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        chrome_driver = "./chromedriver"
        driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
        driver.get("https://sil.ph/ZeMota")
        avatar_type = driver.find_elements_by_xpath('//*[@id="leftPane"]/div[2]/h3[2]')[0].text.title()
        name_on_tc = driver.find_elements_by_xpath('//*[@id="leftPane"]/div[2]/h3[3]')[0].text
        xp = driver.find_elements_by_xpath('//*[@id="leftPane"]/div[2]/h4[1]')[0].text.split("\n")[0][4:]
        team = driver.find_elements_by_xpath('//*[@id="leftPane"]/div[2]/h4[2]')[0].text.split(" ")[1].lower()
        trav_met = driver.find_elements_by_xpath('//*[@id="travelerCard"]/div[2]/div[3]/div[2]/div/h2')[0].text
        nest_reports = driver.find_elements_by_xpath('//*[@id="travelerCard"]/div[2]/div[4]/div[2]/span')[0].text.split(" ")[0]
        pokedex = driver.find_elements_by_xpath('//*[@id="travelerCard"]/div[2]/div[9]/div[3]/p')[0].text[1:]
        play_style = driver.find_elements_by_xpath('//*[@id="travelerCard"]/div[2]/div[10]/div[1]/p/span[2]')[0].text.lower().split(". typically")
        joined = driver.find_elements_by_xpath('//*[@id="travelerCard"]/div[2]/div[3]/div[1]/span')[0].text
        raid_freq = play_style[1]
        play_style = play_style[0][:1].upper() + play_style[0][1:]
        lvl = driver.find_elements_by_xpath('//*[@id="avatarWrap"]/h2')[0].text.split("\n")[1]
        city = driver.find_elements_by_xpath('//*[@id="leftPane"]/div[2]/h3[1]')[0].text.title()
        we_badges = driver.find_elements_by_xpath('//*[@id="awards"]/div/img')
        avatar_img_url = driver.find_elements_by_xpath('//*[@id="avatarWrap"]/img')[0].get_attribute('src')
        avatar_fp = "/home/pjdrm/Desktop/avatar_"+name_on_tc+".png"
        urllib.request.urlretrieve(avatar_img_url, "/home/pjdrm/Desktop/test.png")
        basge_list_str = []
        for badge in we_badges:
            badge_str = badge.get_attribute('src').split("/")[-1].split(".png")[0]
            if badge_str == "brown":
                break
            basge_list_str.append(badge_str)
        print(avatar_fp)
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
        
        traveler_info = {name_on_tc: {"avatar_type": avatar_type,\
                                      "avatar_image_file": avatar_img_url,\
                                      "lvl": lvl,\
                                      "xp": xp,\
                                      "team": team,\
                                      "trav_met": trav_met,\
                                      "nest_reports": nest_reports,\
                                      "pokedex": pokedex,\
                                      "play_style": play_style,\
                                      "city": city,\
                                      "raids": raid_freq,\
                                      "joined": joined,\
                                      "badges": basge_list_str}}
               
        with open(self.traveler_card_db, 'w+') as fp:
            json.dump(traveler_info, fp, indent=4)
        
        driver.close()
        '''
        options = webdriver.FirefoxOptions()
        options.add_argument('-headless')
        driver = webdriver.Firefox(firefox_options=options, executable_path="./geckodriver")
        driver.get("https://sil.ph/ZeMota")
        driver.find_elements_by_xpath('//*[@id="travelerCardWrap"]/div')[0].screenshot("traveller_card.png")
        '''
    def run_discord_bot(self):
        @self.bot.event
        async def on_ready():
            print('Traveler Cards Ready')
        
        @self.bot.command()
        async def tc():
            await self.bot.say(embed=self.get_traveler_card_embeded(self.test_card))
                
        self.bot.run(self.bot_token)

tsr_scraper = TSRScraper()
tsr_scraper.run_discord_bot()
#tsr_scraper.scrape_traveler()