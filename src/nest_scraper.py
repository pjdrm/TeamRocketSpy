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
import discord
from discord.ext import commands

def load_geofences(file_path):
    with open(file_path) as f:
        nests = eval(f.read())
        for nest in nests:
            polygon_pts = nest["path"]
            polygon = Polygon(polygon_pts)
            nest["polygon"] = polygon
    return nests
    
def inside_geofence(polygon, point):
    lat = point[0]
    lon = point[1]
    point = Point(lat, lon) # create point
    is_inside = point.within(polygon)
    return is_inside
    
def find_geofence(geofences, point):
    for geofence in geofences:
        polygon = geofence["polygon"]
        if inside_geofence(polygon, point):
            return geofence["name"]
    return None

def find_nesting_mon(spawns, nest_name, black_mon_list):
    spawn_counts = Counter(spawns)
    ordered_spawn_counts = spawn_counts.most_common(5)
    ordered_spawn_counts.reverse()
    nest_mon = None
    print("Finding nesting species for %s" % nest_name)
    for mon_id, mon_count in ordered_spawn_counts:
        mon_name = POKE_INFO[str(mon_id)]["name"]
        print("species: %s count: %d"%(mon_name, mon_count))
        if mon_name not in black_mon_list:
            nest_mon = mon_name
    if nest_mon is None:
        print("WARNING: could not find nest pokemon")
    return nest_mon
        
def assign_spawns(geofences, spawns):
    nests = {}
    for spawn in spawns:
        gf_name = find_geofence(geofences, spawn["point"])
        if gf_name is None:
            continue
        if gf_name not in nests:
            nests[gf_name] = []
        nests[gf_name].append(spawn["pokemon_id"])
    for geofence in geofences:
        name = geofence["name"]
        if name not in nests:
            print("WARNING: no spawn points for nest %s" % name)
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

async def report_nest(nest_channel, nest_name, nesting_mon, nest_center, api_key):
    print("Reporting nest %s" % nest_name)
    nest_title = nest_name+" is a "+nesting_mon+" nest"
    title_url = "https://www.google.com/maps/search/?api=1&query="+str(nest_center[0])+"%2C"+str(nest_center[1])
    nest_embed=discord.Embed(title=nest_title, url=title_url)
    nest_img_path = "https://maps.googleapis.com/maps/api/staticmap?size=600x300&markers=color:red%7Clabel:%7C"+str(nest_center[0])+","+str(nest_center[1])+"&key="+api_key
    mon_img = "https://raw.githubusercontent.com/pjdrm/TeamRocketSpy/master/config/pokemon-icons/"+nesting_mon+".png"
    nest_embed.set_thumbnail(url=mon_img)
    nest_embed.set_image(url=nest_img_path)
    await nest_channel.send(embed=nest_embed)
    
def find_nests(tr_spy_config):
    '''
    nest_config_path = tr_spy_config["nest_config_path"]
    mon_black_list = tr_spy_config["nest_mon_black_list"]
    geofences = load_geofences(nest_config_path)
    spawns = get_spawns(tr_spy_config)
    nests = assign_spawns(geofences, spawns)
    for name in nests:
        nestig_mon = find_nesting_mon(nests[name], name, mon_black_list)
        if nestig_mon is not None:
            print("%s is a %s nest"%(name, nestig_mon))
            FOUND_NESTS.append([name, nestig_mon])
    '''
    global FOUND_NESTS, NEST_CHANNEL_ID, API_KEY
    FOUND_NESTS = [["Alameda", "numel", [38.7372004,-9.1317359]]]
    NEST_CHANNEL_ID = tr_spy_config["nest_channel_id"]
    API_KEY = tr_spy_config["maps_api_key"]
    bot.run(tr_spy_config["bot_token"])

bot = commands.Bot(command_prefix="$")
    
@bot.event
async def on_ready():
    print("Going to report nests to Poketrainers")
    print(NEST_CHANNEL_ID)
    nest_channel = bot.get_channel(NEST_CHANNEL_ID)
    for nest_name, nestig_mon, nest_center in FOUND_NESTS:
        await report_nest(nest_channel, nest_name, nestig_mon, nest_center, API_KEY)
        await bot.close()

with open("./config/pokemon.json") as data_file:    
    POKE_INFO = json.load(data_file)
        
        
with open("./config/tr_spy_config.json") as data_file:    
    tr_spy_config = json.load(data_file)
   
FOUND_NESTS = []
NEST_CHANNEL_ID = None
API_KEY = None
find_nests(tr_spy_config)
