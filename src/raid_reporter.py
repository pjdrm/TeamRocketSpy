'''
Created on Feb 19, 2018

@author: pjdrm
'''
import discord
from discord.ext import commands
import json
import unicodedata
import time

TESTS_RAIDS = [{'level': '5', 'raid_starts_in': '28', 'gym_name': 'Mural Cacilheiro', 'hatched': False},\
               {'raid_ends_in': '8', 'move_set': ['Dragon Tail', 'Sky Attack'], 'hatched': True, 'gym_name': 'Mural Cacilheiro', 'level': '5', 'boss': 'Lugia'}]

class RaidReportBot():
    
    def __init__(self):
        self.issued_raids = {}
        self.active_raids = self.load_existing_raids()
        self.gyms_meta_data = json.load(open("gyms-metadata.json"))
        self.regions, self.region_map = self.load_region_map("region-map.json")
        self.gyms = self.load_gyms("gyms.json", self.region_map)
        self.bot_token = "NDIyODM5NTgzODc3NjI3OTA1.DYhnlA.Ax_cAy7J4KoPHbD-vjApwC_4l6c"
        self.bot = commands.Bot(command_prefix="%", description='RaidReportBot')
        self.run_discord_bot()
    
    def load_existing_raids(self):
        return {} #TODO: actually crawl list of existing channels to get active raids
    
    def load_gyms(self, gyms_file, region_map):
        gyms_json = json.load(open(gyms_file))
        gyms = {}
        for gym_dic in gyms_json:
            if gym_dic["gymId"] in region_map:
                gyms[gym_dic["gymName"]] = gym_dic["gymId"]
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
            raid_info["raid_ends_in"] = desc_split[3].split("hours ")[1].split(" min")[0]
            raid_info["level"] = raid_embed["title"].split("Level ")[1].split(" ")[0]
            raid_info["hatched"] = True
        else:
            raid_info["raid_starts_in"] = desc_split[1].split("hours ")[1].split(" min")[0]
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
        raid_channel_name = unicodedata.normalize('NFKD', raid_channel_name)
        raid_channel_name = raid_channel_name.replace("/", "-").replace("(", "").replace(")", "").replace(" ", "-").lower()
        return raid_channel_name
    
    def channel_2_raid_channel_name_short(self, channel):
        raid_channel_name_short = channel.name
        if raid_channel_name_short.startswith("tier"):
            raid_channel_name_short = raid_channel_name_short.split("tier-")[1][2:]
        else:
            raid_channel_name_short = raid_channel_name_short.split("-")[1:]
            raid_channel_name_short = "-".join(raid_channel_name_short)
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
            time_command = ""
            if raid_info["hatched"]:
                time_command = "!left " + raid_info["raid_ends_in"]
            else:
                time_command = "!hatch " + raid_info["raid_starts_in"]
            time.sleep(.5)
            await self.bot.send_message(gym_channel, time_command)
            await self.bot.send_message(gym_channel, "!leave")
            self.issued_raids.pop(raid_channel_name)
    
    def remove_active_raid(self, channel):
        rc_short_name = self.channel_2_raid_channel_name_short(channel)
        self.active_raids.pop(rc_short_name)
            
    def report_raid(self, gym_channel_name, raid_info):
        self.issued_raids[gym_channel_name] = raid_info
        
    async def create_raid(self, raid_info):
        print("Creating raid: %s" % str(raid_info))
        raid_channel_name = self.gym_name_2_raid_channel_name_short(raid_info["gym_name"])
        if raid_channel_name in self.active_raids and raid_info["hatched"]:
            gym_channel = self.get_gym_channel(raid_channel_name)
            if gym_channel.name.startswith(("tier")):
                await self.bot.send_message(gym_channel, "!boss "+raid_info["boss"])
        else:
            regional_channel = self.get_regional_channel(raid_info["gym_name"])
            disc_channel = self.regional_channel_dict[regional_channel]
            create_raid_command = self.get_create_raid_command(raid_info)
            self.report_raid(raid_channel_name, raid_info)
            await self.bot.send_message(disc_channel, create_raid_command)
            
    def run_discord_bot(self):
        @self.bot.event
        async def on_ready():
            print('RaidReportBot Ready')
            self.regional_channel_dict = self.load_regional_channels(self.regions)
            await self.read_channel_messages("raid-spotter")
        
        @self.bot.event
        async def on_channel_create(channel):
            print("New Raid created %s" % channel.name)
            await self.add_active_raid(channel)
            
        @self.bot.event
        async def on_channel_delete(channel):
            print("Raid Ended created %s" % channel.name)
            self.remove_active_raid(channel)
            
        @self.bot.command()
        async def test(raid_id):
            await self.create_raid(TESTS_RAIDS[int(raid_id)])
                
        self.bot.run(self.bot_token)

raid_bot = RaidReportBot()