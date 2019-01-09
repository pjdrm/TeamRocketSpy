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
import mysql.connector

from selenium.webdriver import ActionChains
import time

class WeatherBot():
    
    def __init__(self, tr_spy_config_path="./config/tr_spy_config.json",
                       log_file="./weather_forecasts/acu/forecast_log.txt",
                       ingame_weather_log_file="./weather_forecasts/ingame/forecast_log.txt"):
        self.ingame_weather_log_file = ingame_weather_log_file
        with open(tr_spy_config_path) as data_file:    
            self.tr_config = json.load(data_file)
        self.scrape_accu = self.tr_config["scrape_accu"]
        self.scrape_mad = self.tr_config["scrape_mad"]
        self.s2_cells_loc_keys = ['273981', '273947']
        self.s2_cells_db_ids = [943841672003846144, 943839472980590592]
        self.accu_weather_url = []
        self.base_url = 'https://www.accuweather.com/en/pt/lisbon/274087/hourly-weather-forecast/'
        for s2c in self.s2_cells_loc_keys:
            self.accu_weather_url.append(self.base_url+s2c)
        self.log_file = log_file
        self.emoji_dict = {}
        self.weather_forecast = {}
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
        PROXY = "154.73.65.129:30713"
        chrome_options.add_argument('--proxy-server=http://%s' % PROXY)
        
        chrome_driver = "./chromedriver"
        self.driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
        self.scrape_weather()
    
    def get_in_game_weather(self, config, s2_cell_id):
        db_config = { "user": config["user"],
                      "password": config["password"],
                      "host": config["host"],
                      "database": config["database"],
                      "raise_on_warnings": True}
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor(buffered=True)
        
        query = "SELECT * FROM weather WHERE s2_cell_id = "+str(s2_cell_id)
        cursor.execute(query)
        in_game_weather = None
        for (id, s2_cell_id, condition, alert_severity, warn, day, updated) in cursor:
            updated = dt.fromtimestamp(updated).strftime("%d-%m-%y %H:%M")
            in_game_weather = "s2_cell_id "+str(s2_cell_id)+" condition "+str(condition)+" updated "+str(updated)
        return in_game_weather
    
    def scrape_in_game_weather(self, scrape_time_stamp):
        with open(self.ingame_weather_log_file, "a+") as f:
            for s2_cell_id in self.s2_cells_db_ids:
                in_game_weather = self.get_in_game_weather(self.tr_config, s2_cell_id)
                if in_game_weather is None:
                    print("No ingame weather in db")
                    return
                f.write(scrape_time_stamp+" "+in_game_weather+"\n")
        print("Ingame weather scraped at %s" % (scrape_time_stamp))
        
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
    
    def scrape_forecast(self, driver, url, weather_forecast, time_carry, retry=False):
        if time_carry > 0 and not retry:
            url += '?hour='+str(time_carry)
        print(url)
        driver.get(url)
        time.sleep(8)
        
        add_button = driver.find_elements_by_xpath('//*[@id="forecast-extended"]/div[5]/div[2]/section[1]/div[3]/div[1]/p[2]')
        if len(add_button) > 0:
            print("clicking add button")
            add_button[0].click()
        if len(driver.find_elements_by_xpath('//*[@id="detail-hourly"]/div/div[2]/table/thead/tr/td[1]/div[1]')) == 0:
            print("WARNING: failed to get forecast, retrying")
            self.scrape_forecast(driver, url, weather_forecast, time_carry, retry=True)
            
        for h in range(1,9):
            w_hour, hour_forecast_dict  = self.get_hour_forecast(driver, h)
            weather_forecast[w_hour+' tc'+str(time_carry)] = hour_forecast_dict
        return weather_forecast
            
    def scrape_weather(self):
        threading.Timer(3500, self.scrape_weather).start()
        current_time_stamp = dt.now()
        current_hour = int(current_time_stamp.strftime('%H'))
        current_time_stamp = current_time_stamp.strftime('%d-%m-%y %H:%M')
        
        if self.scrape_accu:
            self.weather_forecast = {}
            with open(self.log_file, "a+") as log_f:
                for accu_s2cell_url in self.accu_weather_url:
                    self.scrape_forecast(self.driver, accu_s2cell_url, self.weather_forecast, 0)
                    self.scrape_forecast(self.driver, accu_s2cell_url, self.weather_forecast, current_hour+8)
                    self.scrape_forecast(self.driver, accu_s2cell_url, self.weather_forecast, current_hour+16)
                    self.scrape_forecast(self.driver, accu_s2cell_url, self.weather_forecast, current_hour+24)
                    s2cel_id = accu_s2cell_url.split('/')[-1]
                    log_f.write("Time stamp: %s s2cell: %s Forecast: %s\n" % (current_time_stamp, s2cel_id, str(self.weather_forecast)))
            print("Accu weather scraped at %s" % (current_time_stamp))
            #driver.close()
        if self.scrape_mad:
            self.scrape_in_game_weather(current_time_stamp)
        
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

weather_bot = WeatherBot()
