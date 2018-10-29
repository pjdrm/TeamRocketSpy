'''
Created on Oct 26, 2018

@author: root
'''
import s2sphere # cant remember if this is the right name
import requests
from datetime import datetime as dt
import threading
import mysql.connector
import json
import datetime

BASE_URL = 'http://dataservice.accuweather.com/forecasts/v1/hourly/12hour/locationKey?apikey='
ACCU_API_KEY = "ryoixWl5LKS370kngiMw0AGiUA4bjoMD"


def s2_id2coords(s2_id):
    ll = s2sphere.CellId(s2_id).to_lat_lng()
    lat = ll.lat().degrees
    lng = ll.lng().degrees
    print("%f %f"%(lat, lng))

def print_db_weather_points():
    s2_id2coords(943841672003846144)
    s2_id2coords(943839472980590592)
    s2_id2coords(945418371678076928)
    s2_id2coords(943837273957335040)
    s2_id2coords(943835074934079488)
    
def get_weather(locationKey):
    r = requests.get(BASE_URL+ACCU_API_KEY+"&details=true&metric=true&locationKey="+locationKey)
    return str(r.content)

def scrape_weather(locationKeys, out_l, config, s2_cells, out_f_ingame):
    threading.Timer(3500, scrape_weather, [locationKeys, out_l, config, s2_cells, out_f_ingame]).start()
    current_time_stamp = dt.now()
    ts = current_time_stamp.strftime("%d-%m-%y %H:%M")
    print("%s Scraping forecast" % ts)
    for lk, out_f in zip(locationKeys, out_l):
        forecast = get_weather(lk)
        with open(out_f, "a+") as f:
            f.write(ts+" "+forecast+"\n")
    print("Starting in-game weather scrape")
    scrape_in_game_weather(config, s2_cells, out_f_ingame, ts)
            
def get_in_game_weather(config, s2_cell_id):
    db_config = { "user": config["user"],
                  "password": config["password"],
                  "host": config["host"],
                  "database": config["database"],
                  "raise_on_warnings": True}
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor(buffered=True)
    
    query = "SELECT * FROM weather WHERE s2_cell_id = "+str(s2_cell_id)
    cursor.execute(query)
    for (id, s2_cell_id, condition, alert_severity, warn, day, updated) in cursor:
        updated = dt.fromtimestamp(updated).strftime("%d-%m-%y %H:%M")
        in_game_weather = "condition "+str(condition)+" updated "+str(updated)
    return in_game_weather

def scrape_in_game_weather(config, s2_cells, out_files, scrape_time_stamp):
    for s2_cell_id, out_f in zip(s2_cells, out_files):
        in_game_weather = get_in_game_weather(config, s2_cell_id)
        with open(out_f, "a+") as f:
            f.write(scrape_time_stamp+" "+in_game_weather+"\n")
         
            
def parse_weather_report(report):
    forecast_hour = report["DateTime"].split("T")[1].split(":00+")[0]
    desc = report["IconPhrase"]
    temp = str(report["Temperature"]["Value"])+"C"
    wind_speed = str(report["Wind"]["Speed"]["Value"])+"k/h"
    visibility = str(report["Visibility"]["Value"])
    percipitation_prob = str(report["PrecipitationProbability"])
    rain_prob = str(report["RainProbability"])
    snow_prob = str(report["SnowProbability"])
    ice_prob = str(report["IceProbability"])
    return forecast_hour, {"desc": desc,
            "temperature": temp,
            "wind_speed": wind_speed,
            "visibility": visibility,
            "percipitation_prob": percipitation_prob,
            "rain_prob": rain_prob,
            "snow_prob": snow_prob,
            "ice_prob": ice_prob}

def parse_weather_log_file(log_f):
    with open(log_f) as f:
        lins = f.readlines()
        parsed_weather_scrape = {}
        for lin in lins:
            lin_split = lin.split(" b")
            time_stamp = lin_split[0]
            weather_scrape = eval(lin_split[1][1:-2].replace("true", "True").replace("false", "False"))
            parsed_weather_scrape[time_stamp] = {}
            for hour_forecast in weather_scrape:
                forecast_hour, parsed_fc = parse_weather_report(hour_forecast)
                parsed_weather_scrape[time_stamp][forecast_hour] = parsed_fc
    return parsed_weather_scrape
            
def monitor_s2cell_diff_reports(log_files1, log_files2):
    parsed_reports1 = parse_weather_log_file(log_files1)
    parsed_reports2 =parse_weather_log_file(log_files2)
    for time_stamp in parsed_reports1:
        diff_flag = False
        for hour in parsed_reports1[time_stamp]:
            for k in parsed_reports1[time_stamp][hour]:
                v1 = parsed_reports1[time_stamp][hour][k]
                v2 = parsed_reports2[time_stamp][hour][k]
                if v1 != v2:
                    diff_flag = True
                    break
        if diff_flag:
            print("Reports on %s are different:\n%s\n%s"%(time_stamp, parsed_reports1[time_stamp], parsed_reports2[time_stamp]))
    print("Done")
        
    
lk_lisbon_center = "273981"
lk_parque_nacoes = "273947"
#scrape_weather([lk_lisbon_center, lk_parque_nacoes], ["./weather_forecasts/lisbon_center_forecasts.txt", "./weather_forecasts/parque_nacoes_forecasts.txt"])

#parse_weather_log_file("./weather_forecasts/lisbon_center_forecasts.txt")
#monitor_s2cell_diff_reports("./weather_forecasts/lisbon_center_forecasts.txt", "./weather_forecasts/parque_nacoes_forecasts.txt")
#lisbon_center = [38.75482, -9.14566]
#parque_nacoes = [38.76304, -9.05676]
tr_spy_config_path = "./config/tr_spy_config.json"    
with open(tr_spy_config_path) as data_file:    
    config = json.load(data_file)
    
db_config = { "user": config["user"],
                  "password": config["password"],
                  "host": config["host"],
                  "database": config["database"],
                  "raise_on_warnings": True}
out_l_acu = ["./weather_forecasts/acu/lisbon_center_forecasts.txt", "./weather_forecasts/acu/parque_nacoes_forecasts.txt"]
out_f_ingame = ["./weather_forecasts/ingame/lisbon_center_forecasts.txt", "./weather_forecasts/ingame/parque_nacoes_forecasts.txt"]
locationKeys = [lk_lisbon_center, lk_parque_nacoes]
s2_cells = [943841672003846144, 943839472980590592]

scrape_weather(locationKeys, out_l_acu, db_config, s2_cells, out_f_ingame)
