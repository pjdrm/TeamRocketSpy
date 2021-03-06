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
import sys
from asyncio.tasks import sleep
from db_scrapper import scrape_raids, scrape_quests, scrape_invasions
from urllib.request import urlopen
import mysql.connector

GYM_TRANSLATION = {"Fountain (perto av Roma - Entrecampos)": "Fountain (EntreCampos)"}
MOVES_EMOJI = '🏹'
MAP_EMOJI = '🗺'
WARNING_EMOJI = '⚠'
SIDEBAR_EMBED_COLOR = 0x5c7ce5
UNOWN_BOT_ID = 475770444889456640
UNOWN_POKESTOP_ICON = "https://static.pokenavbot.com/imgs/teams/team-unknown-logo-256px.png"
OWNER_ID = 346626368244547584

WELCOME1 = "Olá eu sou o bot Unown. Venho dar-te as boas vindas ao PokeTrainers Lisboa e explicar-te a organização do servidor. O servidor está organizado por regiões de forma a poderes filtrar raids que não te interessam. Para saberes as delimitações exactas de cada região podes consultar o link https://drive.google.com/open?id=1d7-IMaiZCAL8gqEixFt-mxqaMqxjpQXU&usp=sharing. Neste momento ainda não tens acesso a nenhuma das regiões. Para ganhar acesso basta ires ao canal #the-bot-lab e escrever os comandos das regiões onde costumas jogar PoGo:\n\
  `!iam alameda`\
  `!iam parque-das-nacoes`\
  `!iam campo-grande`\
  `!iam marques`\
  `!iam zoo`\
  `!iam belem`\
  `!iam santa-apolonia`"
  
WELCOME2 = "Caso queiras ver todas as regiões podes escrever o comando `!iam all`. No entanto, não recomendamos esta opção devido à grande quantidade de canais de raid. A qualquer momentos podes reconfigurar as regiões que vês. Basta usar o comando `!iamnot <região>` para deixar de a ver (funciona do caso do `all` também).\n\nCoordenar as raids neste servidor é bastante fácil com o bot Professora Bolota. No servidor vais ver canais individuais para as raids que estão activas no momento (por exemplo, #rayquaza-casa-da-moeda). Caso estejas interessado em fazer essa raids só tens de ir ao canal correspondente e clicares no botão :white_check_mark:. A Professora Bolota adiciona-te automaticamente à lista de pessoas que vão à raid. Se houver algum imprevisto e já não podes fazer a raid basta clicar :x:.\n\n**__Todas as raids têm de ser realizadas pessoalmente. Este servidor NÃO é spoofer friendly.__**\n\nCom a informação anterior estás praticamente pronto, antes de começar pedimos apenas que faças os seguintes passos:\n- Ler o canal #regras-obrigatorio-ler\n- Fazer a configuração inicial da equipa (`!iam <nome_equipa>` no canal #the-bot-lab)\n\nDepois de habituares-te ao funcionamento normal do servidor sugerimos que explores outras features que achamos que te podem ser muito úteis. Todas elas estão descritas nos vários canais da categoria Tutoriais Bot. Por exemplo, ser notificado de pokemons/ginásios específicos.\n\nespero que consigas muitas raids com 100% por aqui!"

class UnownBot():
    
    def __init__(self, tr_spy_config_path,
                       fetch_raidmons=False,
                       log_file="./raid_reporter_log.txt"):
        with open(tr_spy_config_path) as data_file:    
            self.tr_spy_config = json.load(data_file)
        
        if fetch_raidmons:
            print("Updating list of raid bosses")
            self.fetch_raid_bosses()
            
        with open(self.tr_spy_config["raidmons_path"]) as f:
            self.raid_bosses = eval(f.readline())
            
        self.tr_spy_config_path= tr_spy_config_path
        self.blocked_tiers = self.tr_spy_config["blocked_tiers"]
        self.allowed_pokemon = self.tr_spy_config["allowed_pokemon"]
        self.auto_hatch_flag = self.tr_spy_config["auto_hatch_flag"]
        self.auto_hatch_boss = self.tr_spy_config["auto_hatch_boss"]
        self.bolota_user_str = self.tr_spy_config["bolota_user_str"]
        self.bolota_id = self.tr_spy_config["bolota_id"]
        self.unown_bot_id = self.tr_spy_config["unown_id"]
        self.owner_id = self.tr_spy_config["owner_id"]
        self.pogo_events_fp = self.tr_spy_config["pogo_events"]
        self.active_quests_channel_id = self.tr_spy_config["active_quests_channel_id"]
        self.report_quests_channel_id = self.tr_spy_config["report_quests_channel_id"]
        self.pa_commons_chan_channel_id = self.tr_spy_config["pa_commons_channel_id"]
        self.pa_rare_chan_channel_id = self.tr_spy_config["pa_rare_channel_id"]
        self.reward_filters = self.tr_spy_config["reward_filters"]
        self.report_log_file = log_file
        self.no_time_end_raids = []
        self.issued_raids = {}
        self.active_raids = None
        self.active_invasions = {}
        self.invasion_channel = None
        self.pokestops = json.load(open(self.tr_spy_config["pokestops"]))
        self.gyms_meta_data = json.load(open("gyms-metadata.json"))
        self.type_emojis = json.load(open("server-emojis.json"))
        self.move_type = json.load(open("pokemon-moves.json"))
        self.regions, self.region_map = self.load_region_map("region-map.json")
        self.gyms = self.load_gyms("gyms.json", self.region_map)
        self.bot_token = self.tr_spy_config["bot_token"]
        self.bot = commands.Bot(command_prefix="$", description='UnownBot')
        self.bot.remove_command("help")
        self.raid_messages = {}
        self.boss_movesets = {}
        self.run_discord_bot()
    
    def fetch_raid_bosses(self):
        data = urlopen('https://raw.githubusercontent.com/Googer/Professor-Pine/main-dev/data/pokemon.json').read() #bytes
        pokemon_list = eval(data.decode('utf-8').replace("true", "True"))
        raid_bosses = []
        for poke in pokemon_list:
            if "name" in poke and "tier" in poke:
                raid_bosses.append(poke["name"].replace("_alola", ""))
        with open(self.tr_spy_config["raidmons_path"], "w+") as f:
            f.write(str(raid_bosses))
        
    def is_raid_channel(self, channel_name):
        channel_name = channel_name.replace("alolan-", "")
        first_word = channel_name.split("-")[0]
        if channel_name.startswith(("egg")) or (channel_name.startswith(("boss"))) or (channel_name.startswith(("expired"))) or (first_word in self.raid_bosses):
            return True
        else:
            return False
        
    def is_raid_annouce(self, message):
            if self.bolota_user_str == str(message.author)\
                and"to return to this raid's regional channel" in message.content:
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
    
    async def load_active_quests(self):
        active_quests = {}
        channel = self.bot.get_channel(self.active_quests_channel_id)
        async for message in channel.history(limit=2000):
            ps_name = message.embeds[0]._author["name"]
            active_quests[ps_name] = True
            #print("Quest load: %s" % ps_name)
        return active_quests
    
    def load_invasion_roles(self):
        invasion_roles = {}
        guild_id = self.bot.guilds[0].id #HACK: assumes bot is only in one server
        roles = self.bot.get_guild(guild_id).roles
        for type in self.type_emojis:
            type_low = type.lower()
            for role in roles:
                role_name = role.name.lower()
                if role_name.startswith("invasion") and type_low in role_name:
                    invasion_roles[type] = "<@&"+str(role.id)+">"
                    break
        return invasion_roles
    
    async def del_reported_invasions(self):
        async for message in self.invasion_channel.history(limit=2000):
            if message.author.id == self.bot.user.id:
                await message.delete()
    
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
            if hasattr(channel, 'send')  and channel.name in regions: #hack to avoid categories
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
            if raid_info["boss"] is not None and raid_info["boss"] in self.allowed_pokemon:
                filtered_raids.append(raid_info)
            if raid_info["level"] is not None and int(raid_info["level"]) in self.blocked_tiers:
                #print("Filtering raid %s" % raid_info)
                continue
            else:
                filtered_raids.append(raid_info)
        return filtered_raids
    
    def filter_quest(self, quest):
        if self.reward_filters == "None" or self.reward_filters[0] == "all":
            return False
        for reward_filter in self.reward_filters:
            if reward_filter in quest["reward"]:
                return False
        return True
    
    async def add_move_handler(self, channel):
        async for message in self.bot.logs_from(channel, limit=500):
                if "Professora Bolota#6934"==str(message.author):
                    if "to return to this raid's regional channel" in message.content:
                        if len(message.reactions) == 9:
                            print("Have moves for %s"%channel.name)
        
    async def check_scraped_raids(self):
        while True:
            time_stamp = dt.now().strftime("%m-%d %H:%M")
            print(time_stamp +" Starting DB raid scrape")
            raid_list = scrape_raids(self.tr_spy_config)
            raid_list = self.filter_tiers(raid_list)
            for raid_info in raid_list:
                await self.create_raid(raid_info)
            await asyncio.sleep(180)
            
    async def check_pogo_quests(self):
        while True:
            print("Quest scraping")
            active_quests = await self.load_active_quests()
            quest_list = scrape_quests(self.tr_spy_config)
            for quest in quest_list:
                if not self.filter_quest(quest) and quest["pokestop"] not in active_quests:
                    await self.create_quest(quest)
                #else:
                #    print("Discarding quest: %s" % quest)
            await self.add_new_pokestops()
            await asyncio.sleep(1800) #30m
            
    async def check_pogo_invasion(self):
            while True:
                time_stamp = dt.now().strftime("%m-%d %H:%M")
                print(time_stamp +" Starting DB Invasion scrape")
                self.clean_active_invasions()
                invasions = scrape_invasions(self.tr_spy_config, self.pokestops)
                for invasion in invasions:
                    if invasion["pokestop"] not in self.active_invasions:
                        await self.create_invasion(invasion)
                await asyncio.sleep(180)
                
    async def check_pogo_events(self):
            while True:
                time_stamp = dt.now().strftime("%m-%d %H:%M")
                print("%s Getting Pogo Events"%time_stamp)
                with open(self.pogo_events_fp) as f:
                    pogo_events = eval(f.readline())
                embed=discord.Embed(title="**Pokemon Go Events:**", color=SIDEBAR_EMBED_COLOR)
                for pogo_event in pogo_events:
                    embed.add_field(name="<:PokeBall:399568284913106944>"+pogo_event["desc"], value=pogo_event["date"], inline=True)
                self.pogo_events_embed = embed
                print(pogo_events)
                await asyncio.sleep(43200) #12h
    
    async def add_new_pokestops(self):
        chan = self.bot.get_channel(self.active_quests_channel_id)
        async for message in chan.history(limit=2000):
                if message.embeds[0].author.icon_url == UNOWN_POKESTOP_ICON:
                    pokestop_name = message.embeds[0].author.name
                    db_config = { "user": self.tr_spy_config["user"],
                                  "password": self.tr_spy_config["password"],
                                  "host": self.tr_spy_config["host"],
                                  "database": self.tr_spy_config["database"],
                                  "raise_on_warnings": True,
                                  "autocommit": True}
                    cnx = mysql.connector.connect(**db_config)
                    cursor = cnx.cursor()
                    query = "select latitude, longitude from pokestop where name='"+pokestop_name.replace("'", '"')+"';"#To match the DB
                    cursor.execute(query)
                    results = cursor.fetchall()
                    if len(results) > 1:
                        continue #TODO: deal with different stops with the same name
                    lat, lon = results[0]
                    add_poi_cmd = '$create poi pokestop "'+pokestop_name+'" '+str(lat)+' '+str(lon)
                    with open('new_pokestops_'+self.tr_spy_config_path.split("/")[-1], 'a') as f:
                        f.write(add_poi_cmd+"\n")
                    
    async def check_pokealarms(self):
        async def del_old_spawns(chan, dt_now):
            async for message in chan.history(limit=2000):
                if message.author.id  != OWNER_ID:
                    alarm_date = message.created_at
                    delta = dt_now-alarm_date
                    if ((delta.days*24*60*60) + delta.seconds)/60.0-60 > 60: #created_at is returning one extra hour for some reason
                        await message.delete()
        while True:
            dt_now = dt.now()
            time_stamp = dt_now.strftime("%m-%d %H:%M")
            print("%s Cleaning pokealarms"%time_stamp)
            pa_commons_chan = self.bot.get_channel(self.pa_commons_chan_channel_id)
            pa_rare_chan = self.bot.get_channel(self.pa_rare_chan_channel_id)
            await del_old_spawns(pa_rare_chan, dt_now)
            await del_old_spawns(pa_commons_chan, dt_now)
            await asyncio.sleep(1800) #30m
            
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
            raid_info["spawn"] = desc_split[1].split("hours ")[1].split(" min")[0] #TODO: use absolute times
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
        raid_channel_name_short = channel.name.replace("alolan-", "").replace("origin-", "").replace("expired-", "")
        if raid_channel_name_short.startswith("egg"):
            raid_channel_name_short = raid_channel_name_short.split("egg-")[1][2:]
        elif raid_channel_name_short.startswith("boss"):
            raid_channel_name_short = raid_channel_name_short.split("boss-")[1][2:]
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
            #Sometimes we dont know when egg hatches
            if raid_info["spawn"] is not None:
                time_command = "!hatch " + raid_info["spawn"]
                await gym_channel.send(time_command, delete_after=2)
            else:
                self.no_time_end_raids.append(gym_channel)
            self.issued_raids.pop(raid_channel_name)
    
    def remove_active_raid(self, channel):
        rc_short_name = self.channel_2_raid_channel_name_short(channel)
        if rc_short_name in self.boss_movesets:
            self.boss_movesets.pop(rc_short_name)
        if rc_short_name in self.active_raids:
            self.active_raids.pop(rc_short_name)
        else:
            print("ERROR: cant find %s in:\n%s"%(rc_short_name, self.active_raids))
            
    def report_raid(self, gym_channel_name, raid_info):
        gym_channel_name = unicodedata.normalize('NFD', gym_channel_name).encode('ascii', 'ignore').decode('utf-8', 'ignore')
        self.issued_raids[gym_channel_name] = raid_info
        
    def get_attack_type(self, attack):
        return self.type_emojis[self.move_type[attack]]
        
    async def report_boss_moveset(self, gym_channel, attack_info, user, user_icon):
        fast_attack = self.get_attack_type(attack_info[0])+" "+attack_info[0]
        charge_attack = self.get_attack_type(attack_info[1])+" "+attack_info[1]
        team = attack_info[2]
        moveset_embed=discord.Embed(title="**Raid Info**", color=SIDEBAR_EMBED_COLOR)
        moveset_embed.add_field(name="Boss Attacks:", value=fast_attack+"\n"+charge_attack, inline=False)
        moveset_embed.set_footer(text="Requested by "+user, icon_url=user_icon)
        if team is not None:
            if team[0] == "M":
                gym_info = "<:mystic:399568286439964672>"
            elif team[0] == "V":
                gym_info = "<:valor:399568286351753228>"
            else:   
                gym_info = "<:instinct:399568286033117197>"
            gym_info += " Team "+team
            moveset_embed.add_field(name="Gym Control:", value=gym_info, inline=False)
        await gym_channel.send(embed=moveset_embed)
        
    async def get_raid_annouce(self, gym_channel):
        async for message in gym_channel.history():
            if self.is_raid_annouce(message):
                return message
        return None
        
    async def create_raid(self, raid_info):
        if raid_info["boss"] is None and raid_info["level"] == '5' and self.auto_hatch_flag:
            #print("Auto-hatching tier 5 in %s" % raid_info["gym_name"])
            raid_info["hatched"] = True
            raid_info["boss"] = self.auto_hatch_boss
        
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
        if raid_channel_name in self.issued_raids:
            return #there might be too many raids and Bolota taking too much time to create them
        
        is_active_raid = raid_channel_name in self.active_raids
        
        if 'move_set' in raid_info:
            self.boss_movesets[raid_channel_name] = raid_info['move_set']
        #print(raid_channel_name)
        #print(self.active_raids)
        
        if is_active_raid and raid_channel_name in self.no_time_end_raids:
            if raid_info["raid_ends_in"] is not None:
                print("Setting time for raid %s"%raid_channel_name)
                gym_channel = self.get_gym_channel(raid_channel_name)
                time.sleep(10)
                await gym_channel.send("!hatch " + raid_info["spawn"])
                self.no_time_end_raids.pop(raid_channel_name)
            
        if is_active_raid and raid_info["hatched"]:
            gym_channel = self.get_gym_channel(raid_channel_name)
            if gym_channel.name.startswith(("egg")) or gym_channel.name.startswith(("boss")):
                print("Setting raid boss: %s" % str(raid_info))
                await gym_channel.send("!boss "+raid_info["boss"], delete_after=2)
            if raid_channel_name in self.boss_movesets: #case where we first created a raid and later found out the boss moveset
                raid_annouce_msg = await self.get_raid_annouce(gym_channel)
                if MOVES_EMOJI not in raid_annouce_msg.reactions:
                    await raid_annouce_msg.add_reaction(MOVES_EMOJI)
                    
        elif not is_active_raid:
            regional_channel = self.get_regional_channel(raid_info["gym_name"])
            print("Creating raid: %s in Regional channel: %s" % (raid_info, regional_channel))
            disc_channel = self.regional_channel_dict[regional_channel]
            create_raid_command = self.get_create_raid_command(raid_info)
            self.report_raid(raid_channel_name, raid_info)
            await disc_channel.send(create_raid_command)
    
    async def create_quest(self, quest_info):
        print("Quest reporting: %s" % quest_info)
        quest_cmd = '$quest '+quest_info["reward"]+' "'+quest_info["pokestop"]+'" "'+quest_info["goal"]+'"'
        channel = self.bot.get_channel(self.report_quests_channel_id)
        await channel.send(quest_cmd)
    
    def clean_active_invasions(self):
        current_time_int = int(time.time())
        pop_stops = []
        for stop_name in self.active_invasions:
            incident_expiration = self.active_invasions[stop_name]
            if current_time_int > incident_expiration:
                pop_stops.append(stop_name)
                
        for stop_name in pop_stops:
            self.active_invasions.pop(stop_name, None)

    async def create_invasion(self, invasion_info):
        stop_name = invasion_info["pokestop"]
        if stop_name not in self.pokestops:
            print("WARNING: no info for pokestop %s" % stop_name)
            return
        
        grunt_type = invasion_info["grunt_type"]
        if grunt_type in self.invasion_roles:
            await self.invasion_channel.send("Found "+self.invasion_roles[grunt_type]+"!", delete_after=invasion_info["del_time"])
            
        self.active_invasions[stop_name] = invasion_info["incident_expiration_int"]
        info_string = "**Address:** "+self.pokestops[stop_name]["address"]+\
                  "\n**Expires at:** "+invasion_info["incident_expiration"]+\
                  "\n**Grunt type:** "+grunt_type
        if grunt_type != "Random":
            info_string += " "+self.type_emojis[grunt_type]
        pokestop_img_path = self.pokestops[stop_name]["img_url"]
        invasion_title = "Google maps directions link"
        title_url = self.pokestops[stop_name]["address_url"]
        author_name = "Invasion at "+stop_name
        invasion_embed=discord.Embed(title=invasion_title, url=title_url, description=info_string, colour=SIDEBAR_EMBED_COLOR)
        invasion_embed.set_author(name=author_name)
        mon_img = "https://raw.githubusercontent.com/cecpk/OSM-Rocketmap/f027d429291ab042cf6e5aa9965e5d009dc64ff1/static/images/pokestop/stop_i.png"
        invasion_embed.set_thumbnail(url=mon_img)
        invasion_embed.set_image(url=pokestop_img_path)
        await self.invasion_channel.send(embed=invasion_embed, delete_after=invasion_info["del_time"])
        
    def run_discord_bot(self):
        @self.bot.event
        async def on_ready():
            print('UnownBot Ready')
            self.regional_channel_dict = self.load_regional_channels(self.regions)
            self.active_raids = self.load_existing_raids()
            self.bot.loop.create_task(self.check_scraped_raids())
            self.bot.loop.create_task(self.check_pogo_quests())
            #self.bot.loop.create_task(self.check_pogo_events()) #TODO: currently broken
            self.bot.loop.create_task(self.check_pokealarms())
            if self.tr_spy_config["invasion_channel_id"] > 0:
                self.invasion_channel = self.bot.get_channel(self.tr_spy_config["invasion_channel_id"])
                self.invasion_roles = self.load_invasion_roles()
                await self.del_reported_invasions()
                self.bot.loop.create_task(self.check_pogo_invasion())
            
        @self.bot.event
        async def on_guild_channel_delete(channel):
            print("Raid Ended created %s" % channel.name)
            self.remove_active_raid(channel)
            
        @self.bot.event
        async def on_raw_reaction_add(payload):
            if payload.user_id == self.bolota_id:
                if payload.emoji.name == WARNING_EMOJI:
                    channel = self.bot.get_channel(payload.channel_id)
                    if channel.name not in self.regions:
                        print("New Raid created %s" % channel.name)
                        #TODO: check auto-hatch
                        await self.add_active_raid(channel)
                    
                if payload.emoji.name == MAP_EMOJI:
                    channel = self.bot.get_channel(payload.channel_id)
                    rc_short_name = self.channel_2_raid_channel_name_short(channel)
                    if rc_short_name in self.boss_movesets:
                        msg = await channel.get_message(payload.message_id)
                        await msg.add_reaction(MOVES_EMOJI)
                        return
                
            if payload.emoji.name == MOVES_EMOJI and payload.user_id != self.unown_bot_id: #this is Unown bot. We want to skip its reactions
                channel = self.bot.get_channel(payload.channel_id)
                msg = await channel.get_message(payload.message_id)
                if self.is_raid_annouce(msg):
                    rc_short_name = self.channel_2_raid_channel_name_short(channel)
                    if rc_short_name in self.boss_movesets:
                        member = msg.guild.get_member(payload.user_id)
                        user = str(member).split('#')[0]
                        avatar_url = member.avatar_url
                        await self.report_boss_moveset(channel, self.boss_movesets[rc_short_name], user, avatar_url)
                        await msg.remove_reaction(MOVES_EMOJI, member)
                return
            
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
                    await channel.send("!auto none")
        
        @self.bot.command(pass_context=True)
        async def events(ctx):
            await ctx.message.channel.send(embed=self.pogo_events_embed)
            
        @self.bot.command(pass_context=True) #TODO: provide an actual list of available commands
        async def help(ctx, *args):
            return #Just to override default help and avoid error with Pokenav (ex. $help link)
        
        @self.bot.event
        async def on_member_join(member):
            await member.send(WELCOME1)
            await member.send(WELCOME2)
    
        @self.bot.event
        async def on_command_error(ctx, error):
            if isinstance(error, commands.CommandNotFound):
                return #just to silently ignore unregistred commands
            
        self.bot.run(self.bot_token)

if __name__ == "__main__":
    fetch_raidmons = False
    tr_spy_config_path = "./config/tr_spy_config.json"
    if len(sys.argv) == 2:
        tr_spy_config_path = sys.argv[1]
    elif len(sys.argv) == 3:
        tr_spy_config_path = sys.argv[1]
        fetch_raidmons = False
        
    raid_bot = UnownBot(tr_spy_config_path, fetch_raidmons=fetch_raidmons)
