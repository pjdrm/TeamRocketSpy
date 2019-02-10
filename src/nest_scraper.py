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

def load_geofences(file_path):
    nests = []
    polygon = None
    gf_name = None
    with open(file_path) as f:
        lins = f.readlines()
        for l in lins:
            if "[" in l:
                if polygon is not None:
                    nests.append({"name": gf_name, "polygon": polygon})
                gf_name = l[1:-2]
                polygon = []
            else:
                lat, lon = l.split(",")
                lat = float(lat)
                lon = float(lon)
                polygon.append((lat, lon))
        nests.append({"name": gf_name, "polygon": polygon})
    return nests
    
def inside_geofence(geofence, point):
    lat = point[0]
    lon = point[1]
    polygon = Polygon(geofence) # create polygon
    point = Point(lat, lon) # create point
    is_inside = point.within(polygon)
    return is_inside
    
def find_geofence(geofences, point):
    for geofence in geofences:
        if inside_geofence(geofence, point):
            return geofence
    return None

def find_nesting_mon(spawns, black_mon_list):
    spawn_counts = Counter(spawns)
    ordered_spawn_counts = sorted(spawn_counts.items(), key=lambda kv: kv[1])
    for mon_id in ordered_spawn_counts:
        mon_name = POKE_INFO[str(mon_id)]["name"]
        if mon_name not in black_mon_list:
            return mon_name
    print("WARNING: could not find nest pokemon")
    return None
        
def assign_spawns(geofences, spawns):
    nests = {}
    for spawn in spawns:
        target_geofence = find_geofence(geofences, spawn["point"])
        if target_geofence is None:
            continue
        gf_name = target_geofence["name"]
        if gf_name not in nests:
            nests[gf_name] = []
        nests[gf_name].append(spawn["pokemon_id"])
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
    
    query = "SELECT pokemon_id, lat, lon FROM sightings"
    cursor.execute(query)
    
    spawns = []
    for (pokemon_id, lat, lon) in cursor:
        spawns.append({"pokemon_id": pokemon_id, "point": (lat, lon)})
    return spawns

with open("./config/pokemon.json") as data_file:    
    POKE_INFO = json.load(data_file)
        
        
'''
geofence = [(38.7365052738808, -9.1430676271793), (38.7365471180395, -9.1417372515079), (38.7352750446586, -9.1414797594425), (38.7351997238137, -9.1426599314091)]
inside_point = (38.7362081, -9.1423313)
outside_point = (38.7350532, -9.143651)
inside_geofence(geofence, inside_point)
inside_geofence(geofence, outside_point)
'''
print(load_geofences("/home/pjdrm/workspace/TeamRocketSpy/config/nests_geofences.txt"))