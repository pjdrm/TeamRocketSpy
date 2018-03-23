'''
Created on Feb 19, 2018

@author: pjdrm
'''
import discord
from discord.ext import commands
import threading

class RaidReportBot():
    
    def __init__(self):
        self.bot_token = "NDIyODM5NTgzODc3NjI3OTA1.DYhnlA.Ax_cAy7J4KoPHbD-vjApwC_4l6c"
        self.bot = commands.Bot(command_prefix="%", description='RaidReportBot')
        self.run_discord_bot()
    
    async def read_cahnnel_messages(self, channel_name):
        print("read_cahnnel_messages")
        for channel in self.bot.get_all_channels():
            print(channel.name)
        channel = discord.utils.find(lambda c: c.name==channel_name, self.bot.get_all_channels())
        async for message in self.bot.logs_from(channel, limit=500):
            print("ECHO : " + message.clean_content)
    
    def run_discord_bot(self):
        @self.bot.event
        async def on_ready():
            print('RaidReportBot Ready')
            await self.read_cahnnel_messages("raid-spotter")
        
        @self.bot.event
        async def on_message(message):
            if message.author != self.bot.user:
                await self.bot.send_message(message.channel, "ECHO: "+message.content)            
        self.bot.run(self.bot_token)

raid_bot = RaidReportBot()