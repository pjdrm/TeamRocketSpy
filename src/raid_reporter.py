'''
Created on Feb 19, 2018

@author: pjdrm
'''
import discord
from discord.ext import commands
import json
import unicodedata
import time
import asyncio
from datetime import datetime as dt
from fuzzywuzzy import process
import signal
import sys
from asyncio.tasks import sleep

TESTS_RAIDS = [{'level': '4', 'raid_starts_in': '28', 'gym_name': 'Globo-FCUL', 'hatched': False},\
               {'raid_ends_in': '8', 'move_set': ['Dragon Tail', 'Sky Attack'], 'hatched': True, 'gym_name': 'Mural Cacilheiro', 'level': '5', 'boss': 'Lugia'}]

POKEMON_LIST = {"registeel": 5,
                "mewtwo": 5,
                "giratina": 5,
                "houndoom": 4,
                "tyranitar": 4,
                "absol": 4,
                "marowak": 4,
                "marowak": 4,
                "houndoom": 4,
                "aggron": 4,
                "togetic": 4,
                "machamp": 3,
                "flareon": 3,
                "porygon": 3,
                "donphan": 3,
                "raichu": 3,
                "claydol": 3,
                "magmar": 3,
                "raichu": 3,
                "alakazam": 3,
                "jynx": 3,
                "starmie": 3,
                "sharpedo": 3,
                "gengar": 3,
                "granbull": 3,
                "kirlia": 2,
                "mawile":2,
                "exeggutor":2,
                "slowbro": 2,
                "sableye": 2,
                "misdreavus": 2,
                "charmander":1,
                "magikarp":1,
                "makuhita":1,
                "meditite":1,
                "drowzee": 1,
                "wailmer": 1,
                "shinx": 1,
                "shuppet": 1,
                "duskull": 1,
                "snorunt": 1,
                "buizel": 1}

BLOCKED_TIERS = [1,2,3]
ALLOW_POKEMON = ["Shinx", "Buizel", "Sharpedo"]

GYM_TRANSLATION = {"Fountain (perto av Roma - Entrecampos)": "Fountain (EntreCampos)"}

class RaidReportBot():
    
    def __init__(self, bot_token,
                       raids_scraped_file,
                       log_file="./raid_reporter_log.txt"):
        
        self.raids_scraped_file = raids_scraped_file
        self.report_log_file = log_file
        self.pokemon_list = POKEMON_LIST #TODO: load a list of pokemon
        self.no_time_en_raids = []
        self.issued_raids = {}
        self.active_raids = None
        self.gyms_meta_data = json.load(open("gyms-metadata.json"))
        self.type_emojis = json.load(open("server-emojis.json"))
        self.move_type = json.load(open("pokemon-moves.json"))
        self.regions, self.region_map = self.load_region_map("region-map.json")
        self.gyms = self.load_gyms("gyms.json", self.region_map)
        self.bot_token = bot_token
        self.bot = commands.Bot(command_prefix="%", description='RaidReportBot')
        self.raid_messages = {}
        self.run_discord_bot()
    
    def is_raid_channel(self, channel_name):
        channel_name = channel_name.replace("alolan-", "")
        first_word = channel_name.split("-")[0]
        if channel_name.startswith(("tier")) or first_word in self.pokemon_list:
            return True
        else:
            return False
                    
    def load_existing_raids(self):
        active_raids = {}
        for channel in self.bot.get_all_channels():
            if self.is_raid_channel(channel.name):
                raid_channel_name_short = self.channel_2_raid_channel_name_short(channel)
                active_raids[raid_channel_name_short] = channel
                print("Loaded raid %s" % raid_channel_name_short)
        return active_raids
    
    def load_gyms(self, gyms_file, region_map):
        gyms_json = json.load(open(gyms_file))
        gyms = {}
        for gym_dic in gyms_json:
            if gym_dic["gymId"] in region_map:
                gym_name = gym_dic["gymName"].strip()
                gyms[gym_name] = gym_dic["gymId"]
                if gym_dic["gymId"] in self.gyms_meta_data and "nickname" in self.gyms_meta_data[gym_dic["gymId"]]:
                    gyms[self.gyms_meta_data[gym_dic["gymId"]]["nickname"]] = gym_dic["gymId"]
        return gyms
    
    def load_region_map(self, region_file):
        region_map_json = json.load(open(region_file))
        regions = region_map_json.keys()
        region_map = {}
        for region in region_map_json:
            for gym_id in region_map_json[region]:
                region_map[gym_id] = region
        return regions, region_map
    
    def load_regional_channels(self, regions):
        regional_channels = {}
        for channel in self.bot.get_all_channels():
            if channel.name in regions:
                regional_channels[channel.name] = channel
        return regional_channels
    
    def check_if_gyms_exist(self, gym_names):
        not_found_gyms = []
        for gym_name in gym_names:
            if gym_name not in self.gyms:
                not_found_gyms.append(gym_name)
        if len(not_found_gyms) > 0:
            print("Could not find the following gyms:")
            for gym_name in not_found_gyms:
                print(gym_name)
        else:
            print("Found all gyms!")
    
    def filter_tiers(self, raid_list):
        filtered_raids = []
        for raid_info in raid_list:
            if raid_info["boss"] is not None and raid_info["boss"] in ALLOW_POKEMON:
                filtered_raids.append(raid_info)
            if raid_info["level"] is not None and int(raid_info["level"]) in BLOCKED_TIERS:
                #print("Filtering raid %s" % raid_info)
                continue
            else:
                filtered_raids.append(raid_info)
        return filtered_raids
    
    async def check_scraped_raids(self):
        while True:
            time_stamp = dt.now().strftime("%m-%d %H:%M")
            with open(self.raids_scraped_file) as raids_f:
                raid_list = eval(raids_f.readlines()[0])
            
            raid_list = self.filter_tiers(raid_list)
            for raid_info in raid_list:
                await self.create_raid(raid_info)
            await asyncio.sleep(60)
        
    async def read_channel_messages(self, channel_name):
        print("read_channel_messages")
        #for channel in self.bot.get_all_channels():
        #    print(channel.name)
        channel = discord.utils.find(lambda c: c.name==channel_name, self.bot.get_all_channels())
        gyms_to_check = []
        raid_alerts = []
        async for message in self.bot.logs_from(channel, limit=100, reverse=True):
            if len(message.embeds) > 0:
                raid_info = self.parse_raid_message(message.embeds[0])
                if raid_info["gym_name"] in self.gyms:
                    raid_alerts.append(raid_info)
                    gyms_to_check.append(raid_info["gym_name"])
                    raid_command = self.get_create_raid_command(raid_info)
                    print(raid_command + " " + self.gym_name_2_raid_channel_name_short(raid_info["gym_name"]))
        
        for raid_info in raid_alerts:
            if raid_info["gym_name"] == "Mural Cacilheiro":
                print(raid_info)
                #await self.create_raid(raid_info)
        self.check_if_gyms_exist(gyms_to_check)
                
    def parse_raid_message(self, raid_embed):
        raid_info = {}
        desc_split = raid_embed["description"].split("\n")
        gym_name = desc_split[0].replace("*", "")[:-1]
        raid_info["gym_name"] = gym_name
        if len(desc_split) == 4:
            raid_info["boss"] = desc_split[1]
            raid_info["move_set"] = desc_split[2].split("**Moves:** ")[1].split(" / ")
            raid_info["raid_ends_in"] = desc_split[3].split("hours ")[1].split(" min")[0] #TODO: use absolute times
            raid_info["level"] = raid_embed["title"].split("Level ")[1].split(" ")[0]
            raid_info["hatched"] = True
        else:
            raid_info["raid_starts_in"] = desc_split[1].split("hours ")[1].split(" min")[0] #TODO: use absolute times
            raid_info["level"] = raid_embed["title"].split("Level ")[1].split(" ")[0]
            raid_info["hatched"] = False
            
        return raid_info
    
    def get_regional_channel(self, gym_name):
        gym_id = self.gyms[gym_name]
        region = self.region_map[gym_id]
        return region
        
    def get_create_raid_command(self, raid_info):
        create_raid_command = "!raid "
        if not raid_info["hatched"]:
            create_raid_command += raid_info["level"]
        else:
            create_raid_command += raid_info["boss"]
        create_raid_command += " " + raid_info["gym_name"]
        return create_raid_command
    
    def gym_name_2_raid_channel_name_short(self, gym_name):
        gym_id = self.gyms[gym_name]
        if gym_id in self.gyms_meta_data and "nickname" in self.gyms_meta_data[gym_id]:
            raid_channel_name = self.gyms_meta_data[gym_id]["nickname"]
        else:
            raid_channel_name = gym_name
        raid_channel_name = unicodedata.normalize('NFD', raid_channel_name).encode('ascii', 'ignore').decode('utf-8', 'ignore')
        raid_channel_name = raid_channel_name.replace("?", "")\
                                             .replace(",", "")\
                                             .replace(".", "")\
                                             .replace(" - ", "-")\
                                             .replace("/", "-")\
                                             .replace("(", "")\
                                             .replace(")", "")\
                                             .replace(" & ", "-")\
                                             .replace(" ", "-").lower()
        return raid_channel_name
    
    def channel_2_raid_channel_name_short(self, channel):
        raid_channel_name_short = channel.name.replace("alolan-", "")
        if raid_channel_name_short.startswith("tier"):
            raid_channel_name_short = raid_channel_name_short.split("tier-")[1][2:]
        else:
            raid_channel_name_short = raid_channel_name_short.split("-")[1:]
            raid_channel_name_short = "-".join(raid_channel_name_short)
        raid_channel_name_short = unicodedata.normalize('NFD', raid_channel_name_short).encode('ascii', 'ignore').decode('utf-8', 'ignore')
        return raid_channel_name_short
    
    def get_gym_channel(self, raid_channel_name):
        return self.active_raids[raid_channel_name]
    
    async def add_active_raid(self, channel):
        raid_channel_name = self.channel_2_raid_channel_name_short(channel)
            
        if raid_channel_name not in self.active_raids.keys():
            self.active_raids[raid_channel_name] = channel
            
        if raid_channel_name in self.issued_raids.keys():
            gym_channel = self.get_gym_channel(raid_channel_name)
            raid_info = self.issued_raids[raid_channel_name]
            time_command = None
            if raid_info["hatched"]:
                #Sometimes we dont know when raid ends
                if raid_info["raid_ends_in"] is not None:
                    time_command = "!left " + raid_info["raid_ends_in"]
            else:
                #Sometimes we dont know when egg hatches
                if raid_info["raid_starts_in"] is not None:
                    time_command = "!hatch " + raid_info["raid_starts_in"]
            time.sleep(.7)
            if time_command is not None:
                time_message = await self.bot.send_message(gym_channel, time_command)
                await asyncio.sleep(0.5)
                await self.bot.delete_message(time_message)
            else:
                self.no_time_en_raids.append(gym_channel)
            #print("LEAVING RAID " + raid_channel_name)
            #await self.bot.send_message(gym_channel, "!leave")
            self.issued_raids.pop(raid_channel_name)
    
    def remove_active_raid(self, channel):
        rc_short_name = self.channel_2_raid_channel_name_short(channel)
        if rc_short_name in self.active_raids:
            self.active_raids.pop(rc_short_name)
        else:
            print("ERROR: cant find %s in:\n%s"%(rc_short_name, self.active_raids))
            
    def report_raid(self, gym_channel_name, raid_info):
        gym_channel_name = unicodedata.normalize('NFD', gym_channel_name).encode('ascii', 'ignore').decode('utf-8', 'ignore')
        self.issued_raids[gym_channel_name] = raid_info
        
    def get_attack_type(self, attack):
        return self.type_emojis[self.move_type[attack]]
        
    async def report_boss_moveset(self, gym_channel, moveset):
        fast_attack = moveset[0]
        fast_attack += " "+self.get_attack_type(fast_attack)
        charge_attack = moveset[1]
        charge_attack += " "+self.get_attack_type(charge_attack)
        moveset_embed=discord.Embed(title="__**Ataques**__:", color=0x399f21)
        moveset_embed.add_field(name="Fast", value=fast_attack)
        moveset_embed.add_field(name="Charge", value=charge_attack)
        await self.bot.send_message(gym_channel, embed=moveset_embed)
        
    async def create_raid(self, raid_info):
        if raid_info["gym_name"] in GYM_TRANSLATION:
            gym_trans = GYM_TRANSLATION[raid_info["gym_name"]]
            print("Translating gym: %s to: %s" % (raid_info["gym_name"], gym_trans))
            raid_info["gym_name"] = gym_trans
        elif raid_info["gym_name"] not in self.gyms:
            query_match = process.extractOne(raid_info["gym_name"], self.gyms.keys())
            gym_name = query_match[0]
            score = query_match[1]
            time_stamp = dt.now().strftime("%m-%d %H:%M")
            warn_str = time_stamp+" Unknown gym: "+raid_info["gym_name"]+" Using: "+gym_name+" Score: "+str(score)
            with open(self.report_log_file, "a+") as f:
                f.write(warn_str+"\n")
            print(warn_str)
            raid_info["gym_name"] = gym_name
            if score <= 86:
                print("Discarded raid")
                return
                
        raid_channel_name = self.gym_name_2_raid_channel_name_short(raid_info["gym_name"])
        is_active_raid = raid_channel_name in self.active_raids
        #print(raid_channel_name)
        #print(self.active_raids)
        
        if is_active_raid and raid_channel_name in self.no_time_en_raids:
            if raid_info["raid_ends_in"] is not None:
                print("Setting time for raid %s"%raid_channel_name)
                gym_channel = self.get_gym_channel(raid_channel_name)
                time.sleep(1)
                await self.bot.send_message(gym_channel, "!left "+raid_info["raid_ends_in"])
                self.no_time_en_raids.pop(raid_channel_name)
            
        if is_active_raid and raid_info["hatched"]:
            gym_channel = self.get_gym_channel(raid_channel_name)
            if gym_channel.name.startswith(("tier")):
                print("Setting raid boss: %s" % str(raid_info))
                #time.sleep(1)
                boss_message = await self.bot.send_message(gym_channel, "!boss "+raid_info["boss"])
                await asyncio.sleep(0.5)
                await self.bot.delete_message(boss_message)
            #await self.report_boss_moveset(gym_channel, raprinid_info["move_set"])    
        elif not is_active_raid:
            regional_channel = self.get_regional_channel(raid_info["gym_name"])
            print("Creating raid: %s in Regional chanel: %s" % (raid_info, regional_channel))
            disc_channel = self.regional_channel_dict[regional_channel]
            create_raid_command = self.get_create_raid_command(raid_info)
            self.report_raid(raid_channel_name, raid_info)
            #await asyncio.sleep(10) #I think the permissions issue was because I was sending too many messages
            try:
                await self.bot.send_message(disc_channel, create_raid_command)
            except discord.Forbidden as e:
                print("ERROR: got forbidden exception")
                print(str(e))
                self.bot.login(self.bot_token)
                return
            #print("Sent raid command: %s" % create_raid_command)
        
    async def test_permissions(self):
        channel = self.regional_channel_dict["santa-apolonia"]
        while True:
            print("Checking Permissions")
            await self.bot.send_message(channel, "TEST2")
            print("Done Checking")
            await asyncio.sleep(250)
        
    def run_discord_bot(self):
        @self.bot.event
        async def on_ready():
            print('RaidReportBot Ready')
            self.regional_channel_dict = self.load_regional_channels(self.regions)
            self.active_raids = self.load_existing_raids()
            self.bot.loop.create_task(self.check_scraped_raids())
            #self.bot.loop.create_task(self.test_permissions())
            #await self.read_channel_messages("raid-spotter")
        
        @self.bot.event
        async def on_channel_create(channel):
            if channel.name is None:
                return
            print("New Raid created %s" % channel.name)
            await self.add_active_raid(channel)
            
        @self.bot.event
        async def on_channel_delete(channel):
            print("Raid Ended created %s" % channel.name)
            self.remove_active_raid(channel)
            
        @self.bot.command()
        async def test(raid_id):
            await self.create_raid(TESTS_RAIDS[int(raid_id)])
            
        @self.bot.command()
        async def kb():
            print("Going to kill bot")
            self.bot.logout()
            self.bot.close()
            
        @self.bot.command()
        async def autonone():
            for channel in self.bot.get_all_channels():
                if channel.name in "#the-bot-lab":
                    print("Going to autonone")
                    await self.bot.send_message(channel, "!auto none")
            
        self.bot.run(self.bot_token)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        tr_spy_config_path = "./config/tr_spy_config.json"
    else:
        tr_spy_config_path = sys.argv[1]
        
    with open(tr_spy_config_path) as data_file:    
        tr_spy_config = json.load(data_file)
    
    bot_token = tr_spy_config["bot_token"]
    raids_scraped_file = tr_spy_config["raids_scraped_file"]
    raid_bot = RaidReportBot(bot_token, raids_scraped_file)