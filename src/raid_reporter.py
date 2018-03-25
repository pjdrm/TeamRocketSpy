'''
Created on Feb 19, 2018

@author: pjdrm
'''
import discord
from discord.ext import commands
import json

class RaidReportBot():
    
    def __init__(self):
        self.regions, self.region_map = self.load_region_map("region-map.json")
        self.gyms = self.load_gyms("gyms.json", self.region_map)
        self.bot_token = "NDIyODM5NTgzODc3NjI3OTA1.DYhnlA.Ax_cAy7J4KoPHbD-vjApwC_4l6c"
        self.bot = commands.Bot(command_prefix="%", description='RaidReportBot')
        self.run_discord_bot()
    
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
        async for message in self.bot.logs_from(channel, limit=500):
            if len(message.embeds) > 0:
                raid_info = self.parse_raid_message(message.embeds[0])
                if raid_info["gym_name"] in self.gyms:
                    gyms_to_check.append(raid_info["gym_name"])
                    raid_command = self.get_create_raid_command(raid_info)
                    regional_channel = self.get_regional_channel(raid_info["gym_name"])
                    disc_channel = self.regional_channel_dict[regional_channel]
                    print(raid_command + " " + regional_channel)
                    await self.bot.send_message(disc_channel, raid_command)
        self.check_if_gyms_exist(gyms_to_check)
        
                
    def parse_raid_message(self, raid_embed):
        raid_info = {}
        desc_split = raid_embed["description"].split("\n")
        gym_name = desc_split[0].replace("*", "")[:-1]
        raid_info["gym_name"] = gym_name
        if len(desc_split) == 4:
            raid_info["boss"] = desc_split[1]
            raid_info["move_set"] = desc_split[2].split("**Moves:** ")[1].split(" / ")
            raid_info["raid_ends_in"] = desc_split[3].split("hours ")[1].replace(" min ", ":").split(" sec")[0]
            raid_info["level"] = raid_embed["title"].split("Level ")[1].split(" ")[0]
            raid_info["hatched"] = True
        else:
            raid_info["raid_starts_in"] = desc_split[1].split("hours ")[1].replace(" min ", ":").split(" sec")[0]
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
            
    def run_discord_bot(self):
        @self.bot.event
        async def on_ready():
            print('RaidReportBot Ready')
            self.regional_channel_dict = self.load_regional_channels(self.regions)
            await self.read_channel_messages("raid-spotter")
        
        @self.bot.event
        async def on_message(message):
            if message.author != self.bot.user:
                await self.bot.send_message(message.channel, "ECHO: "+message.content)
                
        self.bot.run(self.bot_token)

raid_bot = RaidReportBot()