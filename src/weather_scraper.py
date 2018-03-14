'''
Created on Feb 19, 2018

@author: pjdrm
'''
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import discord
from discord.ext import commands
import json
from datetime import datetime
import threading
import copy

class WeatherBot():
    
    def __init__(self, config):
        with open(config) as config_file:
            config_dict = json.load(config_file)
        
        self.weather_lookup_table = config_dict["weather_lookup_table"]
        self.weather_consts = config_dict["weather_consts"]
        self.bot_token = config_dict["bot_token"]
        self.accu_weather_url = config_dict["accu_weather_url"]
        self.bot = commands.Bot(command_prefix=config_dict["prefix"], description='WeatherBot')
        self.weather_forecast = {}
        self.cached_weather_forecast = []
        self.scrape_weather()
    
    def get_hour_forecast(self, driver, h):
        w_hour = driver.find_elements_by_xpath('//*[@id="detail-hourly"]/div/div[2]/table/thead/tr/td['+str(h)+']/div[1]')[0].text[:-2]
        w_forecast = driver.find_elements_by_xpath('//*[@id="detail-hourly"]/div/div[2]/table/tbody/tr[1]/td['+str(h)+']/span')[0].text
        rain_prob = int(driver.find_elements_by_xpath('//*[@id="detail-hourly"]/div/div[3]/table/tbody/tr[1]/td['+str(h)+']/span')[0].text[:-1])
        wind_speed = int(driver.find_elements_by_xpath('//*[@id="detail-hourly"]/div/div[2]/table/tbody/tr[4]/td['+str(h)+']/span')[0].text.split(" ")[0])
        if rain_prob > 50:
            w_forecast = "Rainy"
        elif wind_speed >= 33:
            w_forecast = "Windy"
        return int(w_hour), w_forecast, str(rain_prob)+"%", str(wind_speed)+"km/h"
        
    def scrape_weather(self):
        threading.Timer(3500, self.scrape_weather).start()
        current_time_stamp = datetime.now()
        # instantiate a chrome options object so you can set the size and headless preference
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument("user-agent=WIP")
        
        chrome_driver = "./chromedriver"
        driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
        driver.get(self.accu_weather_url)
        self.weather_forecast = {}
        for h in range(1,8):
            w_hour, w_forecast, rain_prob, wind_speed  = self.get_hour_forecast(driver, h)
            self.weather_forecast[w_hour] = [w_forecast, rain_prob, wind_speed]
        self.cached_weather_forecast.append((current_time_stamp, copy.deepcopy(self.weather_forecast)))
        self.cached_weather_forecast = self.cached_weather_forecast[:5]
        print("Scrape time stamp: %s\nForecast: %s" % (current_time_stamp.strftime('%H:%M'), str(self.weather_forecast)))
        
    def get_debug_weather_reports(self, h):
        forecast = self.weather_forecast[h]
        debug_pogo_weather1 = ""
        for cached_forecast in self.cached_weather_forecast:
            time_stamp = cached_forecast[0]
            rain_prob = forecast[1]
            wind_speed = forecast[2]
            debug_pogo_weather1 += "Time Stamp: " + time_stamp.strftime("%m-%d %H:%M")+\
                                    "\nOriginal desc: " + forecast[0]+\
                                    "\nRain Prob: " + rain_prob + "\nWind Speed: " + wind_speed + "\n\n"
        debug_pogo_weather1 = debug_pogo_weather1[:-2]
        return debug_pogo_weather1
        
    def get_forecast(self):
        current_time_stamp = datetime.now()
        current_hour = current_time_stamp.strftime('%H')
        current_hour_am_pm = int(datetime.strptime(current_hour, "%H").strftime("%I"))
        current_hour = int(current_hour)

        forecast = self.weather_forecast[current_hour_am_pm]
        w_forecast = forecast[0]
        weather_const1 = self.weather_lookup_table[w_forecast]
        pogo_weather1 = self.weather_consts[weather_const1]["description"] +\
                        "\n" + self.weather_consts[weather_const1]["emoji"] + "\n"
        pogo_weather1 += self.get_debug_weather_reports(current_hour_am_pm)
                        
        forecast = self.weather_forecast[current_hour_am_pm+1]
        w_forecast = forecast[0]
        weather_const2 = self.weather_lookup_table[w_forecast]
        pogo_weather2 = self.weather_consts[weather_const2]["description"] +\
                        "\n" + self.weather_consts[weather_const2]["emoji"] + "\n"
        pogo_weather2 += self.get_debug_weather_reports(current_hour_am_pm+1)
        
        h1 = str(current_hour)+ "h"
        h2 = str(current_hour+1)+"h"
        
        embed=discord.Embed(title="__**Previsão do Tempo**__:", color=0x399f21)
        embed.add_field(name=h1, value=pogo_weather1, inline=True)
        embed.add_field(name=h2, value=pogo_weather2, inline=True)
        '''
        if current_time_stamp-self.last_scan_time_stamp:
            thread = threading.Thread(target=self.scrape_weather)
            thread.start()
        '''
        return embed
    
    def run(self):
        @self.bot.event
        async def on_ready():
            print('WeatherBot Ready')
        
        @self.bot.command()
        async def tempo():
            await self.bot.say(embed=self.get_forecast())
            
        self.bot.run(self.bot_token)

weather_bot = WeatherBot("/home/pjdrm/eclipse-workspace/TeamRocketSpy/src/weather_bot_config.json")
weather_bot.run()
    
    