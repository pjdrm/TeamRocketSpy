'''
Created on Feb 19, 2018

@author: pjdrm
'''
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import discord
from discord.ext import commands
import json
from datetime import datetime as dt
import datetime
import threading
import copy

from selenium.webdriver import ActionChains
import time

class WeatherBot():
    
    def __init__(self, config, log_file="./forecast_log.txt", report_log_file="./report_forecast_log.txt", run_d_bot=False):
        self.report_log_file = report_log_file
        #with open(config) as config_file:
        #    config_dict = json.load(config_file)
        #self.weather_lookup_table = config_dict["weather_lookup_table"]
        #self.weather_consts = config_dict["weather_consts"]
        #self.bot_token = config_dict["bot_token"]
        self.accu_weather_url = ["https://www.accuweather.com/en/pt/lisbon/274087/hourly-weather-forecast/273981",
                                 "https://www.accuweather.com/en/pt/lisbon/274087/hourly-weather-forecast/273981?hour=20"]#config_dict["accu_weather_url"]
        self.log_file = log_file
        self.emoji_dict = {}
        #for key in self.weather_consts:
        #    emoji = self.weather_consts[key]["emoji"]
        #    self.emoji_dict[emoji] = key
        self.weather_forecast = {}
        #self.cached_weather_forecast = self.load_forecast_cache(self.log_file)
        self.scrape_weather()
        #self.get_in_game_weather()
        #if run_d_bot:
        #    self.bot = commands.Bot(command_prefix=config_dict["prefix"], description='WeatherBot')
        #    self.run_discord_bot()
    
    def get_in_game_weather(self):
        threading.Timer(3500, self.get_in_game_weather).start()
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument("user-agent=WIP")
        
        chrome_driver = "./chromedriver"
        driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
        driver.get("http://map.pogotuga.club/")
        iframes = driver.find_elements_by_tag_name("iframe")
                        
        driver.switch_to.frame(iframes[1])
        ids = driver.find_elements_by_xpath('//*[@id]')
        for ii in ids:
            #print ii.tag_name
            if "cancel" == ii.get_attribute('id'):
                ii.click()
                #print("Clicked Cancel")
        
        driver.switch_to.default_content()
        driver.find_elements_by_xpath('//*[@class="confirm"]')[0].click()
        #print("Clicked Ok")
        
        found_weather = []
        pokemon_despawn_time = []
        for i in range(3, 400):
            possible_pokemon_wb = driver.find_elements_by_xpath('//*[@id="map"]/div/div/div[1]/div[3]/div[2]/div[3]/div[@class]['+str(i)+']')
            if len(possible_pokemon_wb) == 0:
                break
            else:
                possible_pokemon_wb = possible_pokemon_wb[0]
            hover = ActionChains(driver).move_to_element(possible_pokemon_wb)
            hover.perform()
            time.sleep(.1)
            poke_pop_up = driver.find_elements_by_xpath('//*[@class="pokemon weather-boost"]')
            #poke_name = driver.find_elements_by_xpath('//*[@class="pokemon name"]')[0].text
            #if len(poke_name):
            #    print("Checking weather for %s" % poke_name)
            if len(poke_pop_up) > 0 and len(poke_pop_up[0].text) > 0:
                weather = poke_pop_up[0].text
                time_disppear = driver.find_elements_by_xpath('//*[@class="pokemon disappear"]')[0].text
                time_disppear = time_disppear.split("(")[1].replace(")", "")
                if len(found_weather) == 0 or weather not in found_weather:
                    found_weather.append(weather)
                    pokemon_despawn_time.append(time_disppear)
                if len(found_weather) == 2:
                    break
        for w, ts in zip(found_weather, pokemon_despawn_time):
            print("Weather: %s Time stamp: %s" % (w, ts))
            
        if len(found_weather) > 0:
            in_game_weater = None
            if len(found_weather) == 1:
                #print("Only found weather condition\n")
                in_game_weater = found_weather[0]
                
            else:
                ts1 = dt.strptime(pokemon_despawn_time[0],'%H:%M')
                ts2 = dt.strptime(pokemon_despawn_time[1],'%H:%M')
                #print("Found two weather conditions")
                if ts1.time() > ts2.time():
                    in_game_weater = found_weather[0]
                else:
                    in_game_weater = found_weather[1]
            
            time_stamp = dt.now()
            print("Scrape time stamp: %s In-game weather: %s" % (time_stamp.strftime('%H:%M'), in_game_weater))
            with open(self.report_log_file, "a+") as f:
                time_stamp = dt.now().strftime("%m-%d %H:%M")
                f.write(time_stamp+" "+in_game_weater+"\n")
        else:
            print("WARNING: could not scrape weather")
        driver.close()
                
        
    def get_hour_forecast(self, driver, h):
        w_hour = driver.find_elements_by_xpath('//*[@id="detail-hourly"]/div/div[2]/table/thead/tr/td['+str(h)+']/div[1]')[0].text
        w_forecast = driver.find_elements_by_xpath('//*[@id="detail-hourly"]/div/div[2]/table/tbody/tr[1]/td['+str(h)+']/span')[0].text
        rain_prob = int(driver.find_elements_by_xpath('//*[@id="detail-hourly"]/div/div[3]/table/tbody/tr[1]/td['+str(h)+']/span')[0].text[:-1])
        wind_speed = int(driver.find_elements_by_xpath('//*[@id="detail-hourly"]/div/div[2]/table/tbody/tr[4]/td['+str(h)+']/span')[0].text.split(" ")[0])
        temperature = driver.find_elements_by_xpath('//*[@id="detail-hourly"]/div/div[2]/table/tbody/tr[2]/td['+str(h)+']/span')[0].text 
        real_feel = driver.find_elements_by_xpath('//*[@id="detail-hourly"]/div/div[2]/table/tbody/tr[3]/td['+str(h)+']/span')[0].text
        snow_prob = driver.find_elements_by_xpath('//*[@id="detail-hourly"]/div/div[3]/table/tbody/tr[2]/td['+str(h)+']/span')[0].text
        ice_prob = driver.find_elements_by_xpath('//*[@id="detail-hourly"]/div/div[3]/table/tbody/tr[3]/td['+str(h)+']/span')[0].text
        uv_index = driver.find_elements_by_xpath('//*[@id="detail-hourly"]/div/div[4]/table/tbody/tr[1]/td['+str(h)+']/span')[0].text
        cloud_cover = driver.find_elements_by_xpath('//*[@id="detail-hourly"]/div/div[4]/table/tbody/tr[2]/td['+str(h)+']/span')[0].text
        humidity = driver.find_elements_by_xpath('//*[@id="detail-hourly"]/div/div[4]/table/tbody/tr[3]/td['+str(h)+']/span')[0].text
        dew_point = driver.find_elements_by_xpath('//*[@id="detail-hourly"]/div/div[4]/table/tbody/tr[4]/td['+str(h)+']/span')[0].text
        visibility = driver.find_elements_by_xpath('//*[@id="detail-hourly"]/div/div[4]/table/tbody/tr[5]/td['+str(h)+']/span')[0].text
        hour_forcast_dict = {"forecast_desc": w_forecast,\
                            "rain_prob": rain_prob,\
                            "wind_speed": wind_speed,\
                            "temperature": temperature,\
                            "real_feel": real_feel,\
                            "snow_prob": snow_prob,\
                            "ice_prob": ice_prob,\
                            "uv_index": uv_index,\
                            "cloud_cover": cloud_cover,\
                            "humidity": humidity,\
                            "dew_poit": dew_point,\
                            "visibility": visibility}
        
        return w_hour, hour_forcast_dict
        
    def load_forecast_cache(self, log_file):
        forecast_cache = []
        with open(log_file) as f:
            forecast_logs = f.readlines()
            forecast_logs = forecast_logs[-5:]
        for forecast_log in forecast_logs:
            split_forecast_log = forecast_log.split(" ")
            time_stamp = dt.strptime(split_forecast_log[2]+" "+split_forecast_log[3], "%m-%d %H:%M")
            forecast = eval(forecast_log.split("Forecast: ")[1])
            forecast_cache.append((time_stamp, forecast))
        return forecast_cache
    
    def log_fore_cast(self, time_stamp, fore_cast, log_file):
        with open(log_file, "a+") as f:
            f.write("Time stamp: %s Forecast: %s\n" % (time_stamp.strftime("%m-%d %H:%M"), str(fore_cast)))
    
    def scrape_forecast(self, driver, url, weather_forecast):
        print(url)
        driver.get(url)
        for h in range(1,9):
            w_hour, hour_forecast_dict  = self.get_hour_forecast(driver, h)
            weather_forecast[w_hour] = hour_forecast_dict
        return weather_forecast
            
    def scrape_weather(self):
        threading.Timer(3500, self.scrape_weather).start()
        current_time_stamp = dt.now()
        # instantiate a chrome options object so you can set the size and headless preference
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument("user-agent=WIP")
        
        chrome_driver = "./chromedriver"
        driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
        self.weather_forecast = {}
        self.scrape_forecast(driver, self.accu_weather_url[0], self.weather_forecast)
        self.scrape_forecast(driver, self.accu_weather_url[1], self.weather_forecast)
        self.log_fore_cast(current_time_stamp, self.weather_forecast, self.log_file)
        #self.cached_weather_forecast.append((current_time_stamp, copy.deepcopy(self.weather_forecast)))
        #self.cached_weather_forecast = self.cached_weather_forecast[-5:]
        print("%s" % (current_time_stamp.strftime('%d-%m-%y %H:%M')))
        driver.close()
        
    def get_debug_weather_reports(self, h):
        debug_pogo_weather1 = ""
        for cached_forecast in self.cached_weather_forecast[-2:-1]:
            time_stamp = cached_forecast[0]
            forecast = cached_forecast[1][h]
            debug_pogo_weather1 += "Time Stamp: " + time_stamp.strftime("%m-%d %H:%M")+\
                                    "\nOriginal desc: " + forecast["forecast_desc"]+\
                                    "\nRain Prob: " + str(forecast["rain_prob"]) + "%\nWind Speed: " + str(forecast["wind_speed"]) + "km\h\n\n"
        debug_pogo_weather1 = debug_pogo_weather1[:-2]
        return debug_pogo_weather1
        
    def get_in_game_weather_prediction(self, forecast):
        w_forecast = forecast["forecast_desc"]
        rain_prob = int(forecast["rain_prob"])
        wind_speed = int(forecast["wind_speed"])
        if rain_prob > 50:
            w_forecast = "Rainy"
        elif wind_speed >= 33:
            w_forecast = "Windy"
            
        weather_const = self.weather_lookup_table[w_forecast]
        return weather_const
            
    def get_forecast(self):
        current_time_stamp = dt.now()
        current_hour = current_time_stamp.strftime('%I%p').replace("PM", "pm").replace("AM", "am")
        if current_hour[0] == "0":
            current_hour = current_hour[1:]
        next_hour = current_time_stamp+datetime.timedelta(minutes=60)
        next_hour = next_hour.strftime('%I%p').replace("PM", "pm").replace("AM", "am")
        if next_hour[0] == "0":
            next_hour = next_hour[1:]


        forecast = self.weather_forecast[current_hour]
        weather_const1 = self.get_in_game_weather_prediction(forecast)
        pogo_weather1 = self.weather_consts[weather_const1]["description"] +\
                        "\n" + self.weather_consts[weather_const1]["emoji"] + "\n"
        pogo_weather1 += self.get_debug_weather_reports(current_hour)
                        
        forecast = self.weather_forecast[next_hour]
        weather_const2 = self.get_in_game_weather_prediction(forecast)
        pogo_weather2 = self.weather_consts[weather_const2]["description"] +\
                        "\n" + self.weather_consts[weather_const2]["emoji"] + "\n"
        pogo_weather2 += self.get_debug_weather_reports(next_hour)
        
        embed=discord.Embed(title="__**Previsão do Tempo**__:", color=0x399f21)
        embed.add_field(name=current_hour, value=pogo_weather1, inline=True)
        embed.add_field(name=next_hour, value=pogo_weather2, inline=True)
        '''
        if current_time_stamp-self.last_scan_time_stamp:
            thread = threading.Thread(target=self.scrape_weather)
            thread.start()
        '''
        return embed
    
    def run_discord_bot(self):
        @self.bot.event
        async def on_ready():
            print('WeatherBot Ready')
        
        @self.bot.command()
        async def tempo():
            await self.bot.say(embed=self.get_forecast())
            
        @self.bot.command()
        async def report(weather_report):
            if weather_report not in self.emoji_dict:
                resp = "Não conheço esse tempo. Usa um destes emoji no report: "
                for emoji in self.emoji_dict:
                    resp += emoji + " "
                resp = resp[:-1]
            else:
                with open(self.report_log_file, "a+") as f:
                    time_stamp = dt.now().strftime("%m-%d %H:%M")
                    f.write(time_stamp+" "+self.emoji_dict[weather_report]+"\n")
                resp = "Obrigado pelo report"
            await self.bot.say(resp)
            
        self.bot.run(self.bot_token)

weather_bot = WeatherBot("./private_weather_bot_config.json", run_d_bot=True)
