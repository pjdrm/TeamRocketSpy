'''
Created on Feb 9, 2019

@author: pjdrm
'''
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import mysql.connector
from collections import Counter
import json
import datetime
from datetime import datetime as dt
import discord
from discord.ext import commands
import googlemaps
import urllib.request 
import urllib.parse
from operator import itemgetter
import sys

def load_geofences(tr_cfg):
    nest_config_path = tr_spy_config["nest_config_path"]
    with open(nest_config_path) as f:
        nests = eval(f.read())
        
    if "address" not in nests[0]:
        gmaps = googlemaps.Client(key=tr_cfg["maps_api_key"])
        for nest in nests:
            polygon_pts = nest["path"]
            polygon = Polygon(polygon_pts)
            coords = eval(polygon.representative_point().wkt[6:].replace(" ", ", "))
            address = gmaps.reverse_geocode(coords)[0]["formatted_address"]
            str_split = address.split(", ")
            if len(str_split) == 4:
                address = ", ".join(str_split[1:])
            nest["address"] = address
            nest["center"] = coords
        with open(nest_config_path, "w+") as f:
            f.write(json.dumps(nests, indent=1))

    for nest in nests:
        polygon_pts = nest["path"]
        polygon = Polygon(polygon_pts)
        nest["polygon"] = polygon
    return nests

def create_mad_geofence(tr_cfg):
    nest_config_path = tr_spy_config["nest_config_path"]
    with open(nest_config_path) as f:
        nests = eval(f.read())
    mad_geofence = ""
    for nest in nests:
        mad_geofence += '["'+nest["name"]+'"]\n'
        polygon_pts = nest["path"]
        for pt in polygon_pts:
            mad_geofence += str(pt[0])+", "+str(pt[1])+"\n"
        mad_geofence += "\n"
    with open("mad_geofence.txt", "w+") as f:
            f.write(mad_geofence)
            
def download_static_map_img(tr_cfg, outdir):
    nest_config_path = tr_spy_config["nest_config_path"]
    api_key = tr_cfg["maps_api_key"]
    with open(nest_config_path) as f:
        nests = eval(f.read())
    for nest in nests:
        nest_center = nest["center"]
        nest_img_path = "https://maps.googleapis.com/maps/api/staticmap?size=500x250&markers=color:red%7Clabel:%7C"+str(nest_center[0])+","+str(nest_center[1])+"&key="+api_key
        urllib.request.urlretrieve(nest_img_path, outdir+nest["name"]+".png")
    
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
            return geofence
    return None

def find_nesting_mon(spawns, nest_name, black_mon_list):
    spawn_counts = Counter(spawns)
    ordered_spawn_counts = spawn_counts.most_common(5)
    ordered_spawn_counts.reverse()
    nest_mon = None
    low_count_flag = None
    print("Finding nesting species for %s" % nest_name)
    for mon_id, mon_count in ordered_spawn_counts:
        mon_name = POKE_INFO[str(mon_id)]["name"]
        print("species: %s count: %d"%(mon_name, mon_count))
        if mon_name not in black_mon_list:
            if mon_count > 4:
                nest_mon = mon_name
                low_count_flag = False
            else:
                low_count_flag = True
    if nest_mon is None:
        if low_count_flag:
            print("WARNING: pokemon counts are too low to report nest")
        else:
            print("WARNING: could not find nest pokemon")
    return nest_mon

def get_migration_timestamp():
    current_timestamp = dt.now()
    seed_timestamp = dt.strptime(NEST_MIGRATION_DATE_SEED, '%Y-%m-%d %H:%M')
    prev_migration_ts = seed_timestamp
    while True:
        if seed_timestamp > current_timestamp:
            return prev_migration_ts
        prev_migration_ts = seed_timestamp
        seed_timestamp = seed_timestamp+ datetime.timedelta(days=7)
    
def assign_spawns(geofences, spawns):
    nests = {}
    for spawn in spawns:
        geofence = find_geofence(geofences, spawn["point"])
        if geofence is None:
            continue
        gf_name = geofence["name"]
        if gf_name not in nests:
            nests[gf_name] = {}
            nests[gf_name]["spawns"] = []
            nests[gf_name]["address"] = geofence["address"]
            nests[gf_name]["center"] = geofence["center"]
            nests[gf_name]["color"] = geofence["color"]
        nests[gf_name]["spawns"].append(spawn["pokemon_id"])
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
    
    query = "SELECT id, pokemon_id, lat, lon, updated FROM sightings"
    cursor.execute(query)
    
    spawns = []
    to_del_spawns = []
    migration_timestamp = get_migration_timestamp()
    print(migration_timestamp.strftime('Last migration was on %d, %b %Y'))
    for (id, pokemon_id, lat, lon, updated) in cursor:
        spawn_timestamp = datetime.datetime.fromtimestamp(updated)
        if spawn_timestamp < migration_timestamp:
            to_del_spawns.append(id)
            continue
        spawns.append({"pokemon_id": pokemon_id, "point": (lat, lon)})
        
    del_spawns_query = "DELETE FROM sightings WHERE "
    for id in to_del_spawns:
        del_spawns_query += "id = "+str(id)+" OR "
    del_spawns_query = del_spawns_query[:-3]
    del_spawns_query += ";"
    cursor = cnx.cursor(buffered=True)
    cursor.execute(query)
    return spawns

async def report_nest(nest_channel, nest_name, nesting_mon, nest_center, address, time_stamp, region_color):
    print("Reporting nest %s" % nest_name)
    nest_title = "Directions to "+nest_name
    title_url = "https://www.google.com/maps/search/?api=1&query="+str(nest_center[0])+"%2C"+str(nest_center[1])
    author_name = "Nest "+nest_name
    nest_embed=discord.Embed(title=nest_title, url=title_url, description=address, timestamp=time_stamp, colour=discord.Colour(int(region_color[1:], 16)))
    nest_embed.set_author(name=author_name, icon_url="https://png.icons8.com/color/1600/map-pokemon")
    nest_img_path = "raw.githubusercontent.com/pjdrm/TeamRocketSpy/master/config/nest_img/"+nest_name+".png"
    nest_img_path = "https://"+urllib.parse.quote(nest_img_path)
    mon_img = "https://raw.githubusercontent.com/pjdrm/TeamRocketSpy/master/config/pokemon-icons/"+nesting_mon.lower()+".png"
    nest_embed.set_thumbnail(url=mon_img)
    nest_embed.set_image(url=nest_img_path)
    nest_embed.add_field(name="Nesting Pokemon", value=nesting_mon.title(), inline=True)
    await nest_channel.send(embed=nest_embed)

async def get_current_nests(nest_channel):
    current_nests = {}
    async for message in nest_channel.history():
            pokemon = message.embeds[0]._fields[0]["value"]
            nest_name = message.embeds[0].title.replace("Directions to ", "")
            current_nests[nest_name] = pokemon
    return current_nests
    
def is_nest_migration(current_nests, new_nests):
    same_mon_count = 0
    for nn  in new_nests:
        nest_name = nn[0]
        nestig_mon = nn[1]
        if nest_name in current_nests:
            current_nest_mon = current_nests[nest_name]
            if current_nest_mon == nestig_mon:
                same_mon_count += 1
    if same_mon_count >= 3:
        return False
    else:
        return True
    
def find_nests(tr_spy_config, report_nest_flag):
    global FOUND_NESTS, NEST_CHANNEL_ID, API_KEY, GEOFENCES
    mon_black_list = tr_spy_config["nest_mon_black_list"]
    GEOFENCES = load_geofences(tr_spy_config)
    spawns = get_spawns(tr_spy_config)
    nests = assign_spawns(GEOFENCES, spawns)
    for name in nests:
        nestig_mon = find_nesting_mon(nests[name]["spawns"], name, mon_black_list)
        if nestig_mon is not None:
            print("%s is a %s nest"%(name, nestig_mon))
            FOUND_NESTS.append([name, nestig_mon, nests[name]["center"], nests[name]["address"], nests[name]["color"]])
        print("-----------------")
        
    #FOUND_NESTS = [["Alameda", "numel", [38.7372004,-9.1317359], "Av. Alm. Reis 186, 1900-221 Lisboa"], "#FF5252"]
    NEST_CHANNEL_ID = tr_spy_config["nest_channel_id"]
    if report_nest_flag == 1:
        bot.run(tr_spy_config["bot_token"])

bot = commands.Bot(command_prefix="$")
    
@bot.event
async def on_ready():
    global FOUND_NESTS
    nest_channel = bot.get_channel(NEST_CHANNEL_ID)
    current_nests = await get_current_nests(nest_channel)
    timestamp = dt.now()
    async for message in nest_channel.history():
                await message.delete()
    if is_nest_migration(current_nests, FOUND_NESTS):
        print("Going to report nest migration to PokeTrainers")
        FOUND_NESTS = sorted(FOUND_NESTS, key=itemgetter(4))
        for nest_name, nestig_mon, nest_center, address, region_color in FOUND_NESTS:
            await report_nest(nest_channel, nest_name, nestig_mon, nest_center, address, timestamp, region_color)
    else:
        print("Going to UPDATE nests to PokeTrainers")
        all_nests = []
        for nest_name, nestig_mon, nest_center, address, region_color in FOUND_NESTS:
            if nest_name not in current_nests: #Case where we found a previously unreported nest
                print("New nest: %s" % nest_name)
                nest_info = [nest_name, nestig_mon, nest_center, address, region_color]
                all_nests.append(nest_info)
                
        for nest_name in current_nests:
            nestig_mon = current_nests[nest_name]
            for geofence in GEOFENCES:
                if geofence["name"] == nest_name:
                    nest_center = geofence["center"]
                    address = geofence["address"]
                    region_color = geofence["color"]
                    break
            nest_info = [nest_name, nestig_mon, nest_center, address, region_color]
            all_nests.append(nest_info)
            
        all_nests = sorted(all_nests, key=itemgetter(4))
        for nest_name, nestig_mon, nest_center, address, region_color in all_nests:
            await report_nest(nest_channel, nest_name, nestig_mon, nest_center, address, timestamp, region_color)
    await bot.close()

with open("./config/pokemon.json") as data_file:    
    POKE_INFO = json.load(data_file)
        
        
with open("./config/tr_spy_config.json") as data_file:    
    tr_spy_config = json.load(data_file)
   
FOUND_NESTS = []
NEST_CHANNEL_ID = None
GEOFENCES = None
NEST_MIGRATION_DATE_SEED = "2019-02-21 22:00"

if __name__ == "__main__":
    report_nest_flag = 1
    if len(sys.argv) == 2:
        report_nest_flag = int(sys.argv[1])
    find_nests(tr_spy_config, report_nest_flag)
    #create_mad_geofence(tr_spy_config)
    #download_static_map_img(tr_spy_config, "./config/nest_img/")


