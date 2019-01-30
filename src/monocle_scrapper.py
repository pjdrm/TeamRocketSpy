'''
Created on Oct 8, 2018

@author: ZeMota
'''
import mysql.connector
import json
import datetime
from datetime import datetime as dt, timedelta
import sys
import math

def load_move_protos(move_protos_file):
    with open(move_protos_file) as data_file:
        moves_dict = json.load(data_file)
    moves_dict = {v: k for k, v in moves_dict.items()}
    moves_dict_final = {}
    for id in moves_dict:
        move_name = moves_dict[id].replace("_FAST", "").replace("_", " ").title()
        moves_dict_final[id] = move_name
    return moves_dict_final
        
def get_gym_name(fort_id, cnx):
    cursor = cnx.cursor()
    query = "select name from forts where id="+str(fort_id)+";"
    cursor.execute(query)
    return cursor.fetchone()[0]

def get_pokestop_name(guid, cnx):
    cursor = cnx.cursor()
    query = "select name from pokestops where external_id='"+str(guid)+"';"
    cursor.execute(query)
    return cursor.fetchone()[0].strip()

def get_quest_goal(quest_type, quest_target, quest_condition):
    quest_condition = eval(quest_condition)
    quest_goal = None
    if quest_type == 4:
        #Catch Pokemon quests
        quest_goal = "Catch "+str(quest_target)+" "
        if len(quest_condition) == 0:
            quest_goal += "Pokemon"
        elif "with_pokemon_category" in quest_condition[0] and "pokemon_ids" in quest_condition[0]["with_pokemon_category"]:
            catch_mon_desc = ""
            prev_id = -1
            for pokemon_id in quest_condition[0]["with_pokemon_category"]["pokemon_ids"]:
                if pokemon_id == (prev_id+1):
                    prev_id = pokemon_id
                    continue
                pokemon_name = POKE_INFO[str(pokemon_id)]["name"]
                catch_mon_desc += pokemon_name+" "
                prev_id = pokemon_id
            catch_mon_desc = catch_mon_desc.strip()
            str_split = catch_mon_desc.split(" ")
            str_split[-1] = "or "+str_split[-1]
            for mon_name in str_split:
                quest_goal += mon_name+" "
            quest_goal = quest_goal.strip()
        elif "with_pokemon_type" in quest_condition[0] and "pokemon_type" in quest_condition[0]["with_pokemon_type"]:
            type_mon_desc = ""
            for pokemon_type in quest_condition[0]["with_pokemon_type"]["pokemon_type"]:
                type_desc = TYPE_DICT[pokemon_type]
                type_mon_desc += type_desc+", "
            type_mon_desc = type_mon_desc[:-2]
            if len(quest_condition[0]["with_pokemon_type"]["pokemon_type"]) > 1:
                str_split = type_mon_desc.split(" ")
                str_split[-1] = "or "+str_split[-1]
                for mon_type in str_split:
                    quest_goal += mon_type+" "
            else:
                quest_goal += type_mon_desc+" "
            quest_goal += "Pokemon"
        elif quest_condition[0]["type"] == 3:
            quest_goal += "weather boosted Pokemon"
    elif quest_type == 6:
        #Hatch eggs quests
        if quest_target == 1:
            quest_goal = "Hatch an egg"
        else:
            quest_goal = "Hatch "+str(quest_target)+" eggs"
    elif quest_type == 7:
        #Gym battle quests
        if len(quest_condition) > 0 and quest_condition[0]["type"] == 10:
            quest_goal = "Use a supereffective charged attack in "+str(quest_target)+" gym battles"
        else:
            if quest_target > 1:
                quest_goal = "Battle in a gym "+str(quest_target)+" times"
            else:
                quest_goal = "Battle in a gym"
    elif quest_type == 8:
        #Raid quests
        if len(quest_condition) == 0:
            quest_goal = "Battle in a raid"
        elif quest_target == 1:
            quest_goal = "Win a raid"
        else:
            quest_goal = "Win "+str(quest_target)+" raids"
    elif quest_type == 10:
        quest_goal = "Transfer "+str(quest_target)+" Pokemons"
    elif quest_type == 13:
        #Berry quests
        if len(quest_condition) == 0:
            quest_goal = "Use "+str(quest_target)+" to help catch Pokemon"
        elif quest_condition[0]["with_item"]["item"] == 705:
            quest_goal = "Use "+str(quest_target)+" Pinap Berries while catching Pokemon"
        elif quest_condition[0]["with_item"]["item"] == 701:
            quest_goal = "Use "+str(quest_target)+" Razz Berries to help catch Pokemon"
    elif quest_type == 14:
        #Power up quest
        quest_goal = "Power up a Pokemon "+str(quest_target)+" times"
    elif quest_type == 15:
        #Evolve quests
        if len(quest_condition) > 0:
            if quest_condition[0]["type"] == 11:
                quest_goal = "Use an item to evolve a Pokemon"
            elif "with_pokemon_category" in quest_condition[0]:
                pokemon_name = POKE_INFO[str(quest_condition[0]["with_pokemon_category"][0])]["name"]
                quest_goal = "Evolve "+str(quest_target)+" "+pokemon_name
        elif quest_target == 1:
            quest_goal = "Evolve a Pokemon"
        else:
            quest_goal = "Evolve "+str(quest_target)+" Pokemons"
    elif quest_type == 16:
        #Throw quests
        if quest_condition[0]["type"] == 8 and quest_condition[0]["with_throw_type"]["throw_type"] == 10:
            quest_goal = "Make "+str(quest_target)+" nice throws"
        elif quest_condition[0]["type"] == 8 and quest_condition[0]["with_throw_type"]["throw_type"] == 11:
            quest_goal = "Make "+str(quest_target)+" great throws"
        elif quest_condition[0]["type"] == 14 and quest_condition[0]["with_throw_type"]["throw_type"] == 10:
            quest_goal = "Make "+str(quest_target)+" nice throws in row"
        elif quest_condition[0]["type"] == 14 and quest_condition[0]["with_throw_type"]["throw_type"] == 11:
            quest_goal = "Make "+str(quest_target)+" great throws in a row"
    elif quest_type == 23:
        #Trade quests
        if quest_target == 1:
            quest_goal = "Trade a Pokemon"
        else:
            quest_goal = "Trade "+str(quest_target)+" Pokemons"
    elif quest_type == 24:
        #Gift quests
        quest_goal = "Send "+str(quest_target)+" gifts to friends"
    return quest_goal             
    
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
    
def populate_gym_name(fort_id, db_config):
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor(buffered=True)
    query = "SELECT lat, lon FROM forts where id = "+str(fort_id)
    cursor.execute(query)
    lat_mitm = None
    lon_mitm = None
    for (lat, lon) in cursor:
        lat_mitm = lat
        lon_mitm = lon
    
    with open(GYMS_INFO) as gyms_f:    
        gym_info = json.load(gyms_f)
        
    shortest_dist = 99999
    gym_name = None
    for gym_id in gym_info:
        lat = gym_info[gym_id]["latitude"]
        lon = gym_info[gym_id]["longitude"]
        dist = math.sqrt(((lat_mitm-lat)**2)+((lon_mitm-lon)**2))
        if dist < shortest_dist and dist < 0.001:
            shortest_dist = dist
            gym_name = gym_info[gym_id]["name"]
    cursor.close()
    
    found_name = False
    if gym_name is not None:
        found_name = True
        query = 'UPDATE forts SET name="'+gym_name+'" WHERE id = '+str(fort_id)
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor(buffered=True)
        cursor.execute(query)
        cursor.close()
        print("Found new gym: %s"% gym_name)
    #else:
    #    print("WARNING: could not find gym: %d" % fort_id)
    return found_name, gym_name

def scrape_monocle_db(config):
    current_hour = int(dt.now().strftime("%H"))
    if current_hour < 9:
        return [] #dont want to report and trigger notifications too early, might annoy users
    
    db_config = { "user": config["user"],
                  "password": config["password"],
                  "host": config["host"],
                  "database": config["database"],
                  "raise_on_warnings": True,
                  "autocommit": True}
    
    print("Starting Monocle Scrape")
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor(buffered=True)
    
    query = "SELECT fort_id, level, pokemon_id, time_battle, time_end, move_1, move_2 FROM raids"
    cursor.execute(query)
    
    raid_list = []
    
    for (fort_id, level, pokemon_id, time_battle, time_end, move_1, move_2) in cursor:
        hatched = False
        boss = None
        if pokemon_id is not None:
            boss = POKE_INFO[str(pokemon_id)]["name"].replace("Alolan ", "")
            hatched = True
            
        gym_name = get_gym_name(fort_id, cnx)
        if gym_name is None:
            #print("WARNING: unknown for id: %d" % fort_id)
            found_gym, gym_name = populate_gym_name(fort_id, db_config)
            if not found_gym:
                continue
        raid_starts_in = datetime.datetime.fromtimestamp(time_battle).strftime('%H:%M')
        raid_ends_in = datetime.datetime.fromtimestamp(time_end).strftime('%H:%M')
        
        raid_dict = {'level': str(level), 
                     'boss': boss, 
                     'raid_starts_in': raid_starts_in,
                     'raid_ends_in': raid_ends_in,
                     'gym_name': gym_name,
                     'hatched': hatched}
        if pokemon_id is not None:
            raid_dict["move_set"] = [MOVE_DICT[move_1], MOVE_DICT[move_2]]
        if is_present_raid(raid_dict):
            raid_list.append(raid_dict)
        
    cnx.close()
    return raid_list

def scrape_monocle_quests(config):
    db_config = { "user": config["user"],
                  "password": config["password"],
                  "host": config["host"],
                  "database": config["database"],
                  "raise_on_warnings": True,
                  "autocommit": True}
    print("Starting Monocle Scrape")
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor(buffered=True)
    
    query = "SELECT GUID, quest_timestamp, quest_stardust, quest_pokemon_id, quest_item_id, quest_item_amount, quest_type, quest_target, quest_condition FROM trs_quest"
    cursor.execute(query)
    
    quest_list = []
    
    for (GUID, quest_timestamp, quest_stardust, quest_pokemon_id, quest_item_id, quest_item_amount, quest_type, quest_target, quest_condition) in cursor:
        quest_timestamp = datetime.datetime.fromtimestamp(quest_timestamp).strftime("%Y-%m-%d")
        current_timestamp =dt.now().strftime("%Y-%m-%d")
        if quest_timestamp != current_timestamp:
            print("Filtering old quest from %s" % quest_timestamp)
            continue
        
        if quest_pokemon_id != 0:
            reward = POKE_INFO[str(quest_pokemon_id)]["name"]
        elif quest_stardust > 0:
            reward = '"'+str(quest_stardust)+' Stardust"'
        else:
            reward = '"'+str(quest_item_amount)+" "+ITEMS_DICT[str(quest_item_id)]+'"'
        pokestop = get_pokestop_name(GUID, cnx)
        if pokestop == "unknown":
            print("MAD has not picked up Pokestop name")
            continue
        quest_goal = get_quest_goal(quest_type, quest_target, quest_condition)
        quest_list.append({"pokestop": pokestop, "reward": reward, "goal": quest_goal})
    quest_list = sorted(quest_list, key=lambda k: k["reward"]) 
    return quest_list
            

GYMS_INFO = "./config/gym_info.json"
MOVE_DICT = load_move_protos("./config/proto_moves.json")
with open("./config/pokemon.json") as data_file:    
    POKE_INFO = json.load(data_file)
    
TYPE_DICT = {1: "Normal",
            2: "Fighting",
            3: "Flying",
            4: "Poison",
            5: "Ground",
            6: "Rock",
            7: "Bug",
            8: "Ghost",
            9: "Steel",
            10: "Fire",
            11: "Water",
            12: "Grass",
            13: "Electric",
            14: "Psychic",
            15: "Ice",
            16: "Dragon",
            17: "Dark",
            18: "Fairy"}
        
with open("./config/proto_items.json") as data_file:    
    ITEMS_DICT = json.load(data_file)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        tr_spy_config_path = "./config/tr_spy_config.json"
    else:
        tr_spy_config_path = sys.argv[1]
        
    with open(tr_spy_config_path) as data_file:    
        tr_spy_config = json.load(data_file)
    
    scrape_monocle_db(tr_spy_config)