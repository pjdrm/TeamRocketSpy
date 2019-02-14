'''
Created on Feb 9, 2019

@author: pjdrm
'''
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import mysql.connector
from collections import Counter
import operator
import json
import datetime
from datetime import datetime as dt

def load_geofences(file_path):
    with open(file_path) as f:
        nests = eval(f.read())
        mon_black_list =nests["mon_black_list"]
        nests.pop("mon_black_list")
        for name in nests:
            polygon_pts = nests[name]["polygon"]
            polygon = Polygon(polygon_pts)
            nests[name]["polygon"] = polygon
    return nests, mon_black_list
    
def inside_geofence(polygon, point):
    lat = point[0]
    lon = point[1]
    point = Point(lat, lon) # create point
    is_inside = point.within(polygon)
    return is_inside
    
def find_geofence(geofences, point):
    for name in geofences:
        polygon = geofences[name]["polygon"]
        if inside_geofence(polygon, point):
            return name
    return None

def find_nesting_mon(spawns, black_mon_list):
    spawn_counts = Counter(spawns)
    ordered_spawn_counts = spawn_counts.most_common(30)
    for mon_id, mon_count in ordered_spawn_counts:
        mon_name = POKE_INFO[str(mon_id)]["name"]
        if mon_name not in black_mon_list:
            return mon_name
    print("WARNING: could not find nest pokemon")
    return None
        
def assign_spawns(geofences, spawns):
    nests = {}
    for spawn in spawns:
        gf_name = find_geofence(geofences, spawn["point"])
        if gf_name is None:
            continue
        if gf_name not in nests:
            nests[gf_name] = []
        nests[gf_name].append(spawn["pokemon_id"])
    for name in geofences:
        if name not in nests:
            print("WARNING: no spawn points for nest %s"%name)
    return nests

def get_spawns(config):
    db_config = { "user": config["user"],
                  "password": config["password"],
                  "host": config["host"],
                  "database": config["database"],
                  "raise_on_warnings": True,
                  "autocommit": True}
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor(buffered=True)
    
    query = "SELECT pokemon_id, lat, lon, updated FROM sightings"
    cursor.execute(query)
    
    spawns = []
    current_timestamp = dt.now().strftime("%Y-%m-%d")
    for (pokemon_id, lat, lon, updated) in cursor:
        timestamp_timestamp = datetime.datetime.fromtimestamp(updated).strftime("%Y-%m-%d")
        if timestamp_timestamp != current_timestamp:
            continue
        spawns.append({"pokemon_id": pokemon_id, "point": (lat, lon)})
    return spawns

def find_nests(tr_spy_config):
    nest_config_path = tr_spy_config["nest_config_path"]
    geofences, mon_black_list = load_geofences(nest_config_path)
    spawns = get_spawns(tr_spy_config)
    nests = assign_spawns(geofences, spawns)
    for name in nests:
        nestig_mon = find_nesting_mon(nests[name], mon_black_list)
        if nestig_mon is not None:
            print("%s is a %s nest"%(name, nestig_mon))
    

with open("./config/pokemon.json") as data_file:    
    POKE_INFO = json.load(data_file)
        
        
with open("/home/pjdrm/eclipse-workspace/TeamRocketSpy/config/tr_spy_config.json") as data_file:    
    tr_spy_config = json.load(data_file)
find_nests(tr_spy_config)