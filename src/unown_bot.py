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
from monocle_scrapper import scrape_monocle_db
from urllib.request import urlopen
from pogo_events_scrapper import PogoEventsScrapper

GYM_TRANSLATION = {"Fountain (perto av Roma - Entrecampos)": "Fountain (EntreCampos)"}
MOVES_EMOJI = '🏹'
MAP_EMOJI = '🗺'
WARNING_EMOJI = '⚠'
SIDEBAR_EMBED_COLOR = 0x5c7ce5
UNOWN_BOT_ID = 475770444889456640

WELCOME1 = "Olá eu sou o bot Unown. Venho dar-te as boas vindas ao PokeTrainers Lisboa e explicar-te o funcionamento básico deste servidor. O servidor organiza os canais de coordenação de raids por regiões de forma a poderes filtrar facilmente uma grande parte das raids que não te interessam. Para saberes as delimitações exactas de cada região podes consultar o link https://drive.google.com/open?id=1d7-IMaiZCAL8gqEixFt-mxqaMqxjpQXU&usp=sharing. Neste momento ainda não tens acesso a nenhuma das regiões. Para ganhar acesso basta ires ao canal #the-bot-lab e escrever os comandos das regiões onde costumas jogar PoGo:\n\
  `!iam alameda`\
  `!iam campo-grande`\
  `!iam marques`\
  `!iam zoo`\
  `!iam belem`\
  `!iam santa-apolonia`"
  
WELCOME2 = "Caso queiras ver todas as regiões podes escrever o comando `!iam all`. No entanto, não recomendamos esta opção devido à grande quantidade de canais de raid. A qualquer momentos podes reconfigurar as regiões que vês. Basta usar o comando `!iamnot <região>` para deixar de a ver (funciona do caso do `all` também).\n\nCoordenar as raids neste servidor é bastante fácil com o bot Professora Bolota. No servidor vais ver canais individuais para as raids que estão activas no momento (por exemplo, #rayquaza-casa-da-moeda). Caso estejas interessado em fazer essa raids só tens de ir ao canal correspondente e clicares no botão :white_check_mark:. A Professora Bolota adicionar-te automaticamente à lista de pessoas que vão à raid. Se houver algum imprevisto e já não podes fazer a raid basta clicar :x:.\n\n**__Todas as raids têm de ser realizadas pessoalmente. Este servidor NÃO é spoofer friendly.__**\n\nCom a informação anterior estás praticamente pronto, antes de começar pedimos apenas que faças os seguintes passos:\n- Ler o canal #regras-obrigatorio-ler\n- Fazer a configuração inicial da equipa (`!iam <nome_equipa>` no canal #the-bot-lab)\n\nDepois de te habituares ao funcionamento normal do servidor sugerimos que explores outras features que achamos que te podem ser muito úteis. Todas elas estão descritas nos vários canais da categoria Tutoriais Bot. Por exemplo, ser notificado de pokemons/ginásios específicos.\n\nespero que consigas muitas raids com 100% por aqui!"

class UnownBot():
    
    def __init__(self, tr_spy_config,
                       fetch_raidmons=False,
                       log_file="./raid_reporter_log.txt"):
        if fetch_raidmons:
            print("Updating list of raid bosses")
            self.fetch_raid_bosses()
        with open(tr_spy_config["raidmons_path"]) as f:
            self.raid_bosses = eval(f.readline())
        self.pes = PogoEventsScrapper()
        self.tr_spy_config= tr_spy_config
        self.blocked_tiers = self.tr_spy_config["blocked_tiers"]
        self.allowed_pokemon = self.tr_spy_config["allowed_pokemon"]
        self.auto_hatch_flag = self.tr_spy_config["auto_hatch_flag"]
        self.auto_hatch_boss = self.tr_spy_config["auto_hatch_boss"]
        self.bolota_user_str = self.tr_spy_config["bolota_user_str"]
        self.bolota_id = self.tr_spy_config["bolota_id"]
        self.unown_bot_id = self.tr_spy_config["unown_id"]
        self.report_log_file = log_file
        self.no_time_end_raids = []
        self.reported_movesets = []
        self.issued_raids = {}
        self.active_raids = None
        self.gyms_meta_data = json.load(open("gyms-metadata.json"))
        self.type_emojis = json.load(open("server-emojis.json"))
        self.move_type = json.load(open("pokemon-moves.json"))
        self.regions, self.region_map = self.load_region_map("region-map.json")
        self.gyms = self.load_gyms("gyms.json", self.region_map)
        self.bot_token = tr_spy_config["bot_token"]
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
        with open(tr_spy_config["raidmons_path"], "w+") as f:
            f.write(str(raid_bosses))
        
    def is_raid_channel(self, channel_name):
        channel_name = channel_name.replace("alolan-", "")
        first_word = channel_name.split("-")[0]
        if channel_name.startswith(("tier")) or (first_word in self.raid_bosses):
            return True
        else:
            return False
        
    def is_raid_annouce(self, message):
            if self.bolota_usr_str == str(message.author)\
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
            if raid_info["boss"] is not None and raid_info["boss"] in self.allowed_pokemon:
                filtered_raids.append(raid_info)
            if raid_info["level"] is not None and int(raid_info["level"]) in self.blocked_tiers:
                #print("Filtering raid %s" % raid_info)
                continue
            else:
                filtered_raids.append(raid_info)
        return filtered_raids
    
    async def add_move_handler(self, channel):
        async for message in self.bot.logs_from(channel, limit=500):
                if "Professora Bolota#6934"==str(message.author):
                    if "to return to this raid's regional channel" in message.content:
                        if len(message.reactions) == 9:
                            print("Have moves for %s"%channel.name)
        
    async def check_scraped_raids(self):
        while True:
            time_stamp = dt.now().strftime("%m-%d %H:%M")
            raid_list = scrape_monocle_db(self.tr_spy_config)
            raid_list = self.filter_tiers(raid_list)
            for raid_info in raid_list:
                await self.create_raid(raid_info)
            await asyncio.sleep(60)
            
    async def check_pogo_events(self):
            while True:
                time_stamp = dt.now().strftime("%m-%d %H:%M")
                print("%s Getting Pogo Events"%time_stamp)
                pogo_events = self.pes.scrape_pogo_events()
                embed=discord.Embed(title="**Pokemon Go Events:**", color=SIDEBAR_EMBED_COLOR)
                for pogo_event in pogo_events:
                    embed.add_field(name="<:PokeBall:399568284913106944>"+pogo_event["desc"], value=pogo_event["date"], inline=True)
                self.pogo_events_embed = embed
                print(pogo_events)
                await asyncio.sleep(43200) #12h
            
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
            #Sometimes we dont know when egg hatches
            if raid_info["raid_starts_in"] is not None:
                time_command = "!hatch " + raid_info["raid_starts_in"]
                await gym_channel.send(time_command, delete_after=2)
            else:
                self.no_time_end_raids.append(gym_channel)
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
        
    async def report_boss_moveset(self, gym_channel, moveset, user, user_icon):
        fast_attack = moveset[0]
        fast_attack += " "+self.get_attack_type(fast_attack)
        charge_attack = moveset[1]
        charge_attack += " "+self.get_attack_type(charge_attack)
        moveset_embed=discord.Embed(title="**Boss Attacks**:", color=SIDEBAR_EMBED_COLOR)
        moveset_embed.add_field(name="Fast", value=fast_attack, inline=True)
        moveset_embed.add_field(name="Charge", value=charge_attack, inline=True)
        moveset_embed.set_footer(text="Requested by "+user, icon_url=user_icon)
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
        is_active_raid = raid_channel_name in self.active_raids
        
        if 'move_set' in raid_info:
            self.boss_movesets[raid_channel_name] = raid_info['move_set']
        #print(raid_channel_name)
        #print(self.active_raids)
        
        if is_active_raid and raid_channel_name in self.no_time_end_raids:
            if raid_info["raid_ends_in"] is not None:
                print("Setting time for raid %s"%raid_channel_name)
                gym_channel = self.get_gym_channel(raid_channel_name)
                time.sleep(1)
                await gym_channel.send("!left "+raid_info["raid_ends_in"])
                self.no_time_end_raids.pop(raid_channel_name)
            
        if is_active_raid and raid_info["hatched"]:
            gym_channel = self.get_gym_channel(raid_channel_name)
            if gym_channel.name.startswith(("tier")):
                print("Setting raid boss: %s" % str(raid_info))
                await gym_channel.send("!boss "+raid_info["boss"], delete_after=2)
            if raid_channel_name in self.boss_movesets: #case where we first created a raid and later found out the boss moveset
                raid_annouce_msg = self.get_raid_annouce(gym_channel)
                if raid_channel_name not in self.reported_movesets and MOVES_EMOJI not in raid_annouce_msg.reactions:
                    await raid_annouce_msg.add_reaction(MOVES_EMOJI)
                    self.reported_movesets.append(raid_channel_name)
                    
        elif not is_active_raid:
            regional_channel = self.get_regional_channel(raid_info["gym_name"])
            print("Creating raid: %s in Regional chanel: %s" % (raid_info, regional_channel))
            disc_channel = self.regional_channel_dict[regional_channel]
            create_raid_command = self.get_create_raid_command(raid_info)
            self.report_raid(raid_channel_name, raid_info)
            await disc_channel.send(create_raid_command)
        
    def run_discord_bot(self):
        @self.bot.event
        async def on_ready():
            print('UnownBot Ready')
            self.regional_channel_dict = self.load_regional_channels(self.regions)
            self.active_raids = self.load_existing_raids()
            self.bot.loop.create_task(self.check_scraped_raids())
            self.bot.loop.create_task(self.check_pogo_events())
            
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
                        self.reported_movesets.append(rc_short_name)
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
        fetch_raidmons = sys.argv[1]
    elif len(sys.argv) == 3:
        tr_spy_config_path = sys.argv[1]
        fetch_raidmons = sys.argv[2]
        
    with open(tr_spy_config_path) as data_file:    
        tr_spy_config = json.load(data_file)
    
    raid_bot = UnownBot(tr_spy_config, fetch_raidmons=fetch_raidmons)