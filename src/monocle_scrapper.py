'''
Created on Oct 8, 2018

@author: ZeMota
'''
import mysql.connector
import json
import datetime
import threading
from datetime import datetime as dt, timedelta
import sys

def get_gym_name(fort_id, cnx):
    cursor = cnx.cursor()
    query = "select name from forts where id="+str(fort_id)+";"
    cursor.execute(query)
    return cursor.fetchone()[0]

def is_present_raid(raid_info):
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

def scrape_monocle_db(config):
    with open(config["poke_info"]) as f:
        poke_info = json.load(f)
    raids_scraped_file= config["raids_scraped_file"]
    db_config = { "user": config["user"],
                  "password": config["password"],
                  "host": config["host"],
                  "database": config["database"],
                  "raise_on_warnings": True}
    
    threading.Timer(120, scrape_monocle_db, [config]).start()
    print("Starting Monocle Scrape")
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor(buffered=True)
    
    query = "SELECT fort_id, level, pokemon_id, time_battle, time_end FROM raids"
    cursor.execute(query)
    
    raid_list = []
    
    for (fort_id, level, pokemon_id, time_battle, time_end) in cursor:
        hatched = False
        boss = None
        if pokemon_id is not None:
            boss = poke_info[str(pokemon_id)]["name"].replace("Alolan ", "")
            hatched = True
            
        gym_name = get_gym_name(fort_id, cnx)
        raid_starts_in = datetime.datetime.fromtimestamp(time_battle).strftime('%H:%M')
        raid_ends_in = datetime.datetime.fromtimestamp(time_end).strftime('%H:%M')
        
        raid_dict = {'level': str(level), 
                     'boss': boss, 
                     'raid_starts_in': raid_starts_in,
                     'raid_ends_in': raid_ends_in,
                     'gym_name': gym_name,
                     'hatched': hatched}
        if is_present_raid(raid_dict):
            raid_list.append(raid_dict)
        
    for raid in raid_list:
        print(raid)
        
    with open(raids_scraped_file, "w+") as raids_f:
        raids_f.write(str(raid_list))
    
    cnx.close()
    
if __name__ == "__main__":
    if len(sys.argv) == 1:
        tr_spy_config_path = "./config/tr_spy_config.json"
    else:
        tr_spy_config_path = sys.argv[1]
        
    with open(tr_spy_config_path) as data_file:    
        tr_spy_config = json.load(data_file)
    
    scrape_monocle_db(tr_spy_config)