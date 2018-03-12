'''
Created on Feb 19, 2018

@author: pjdrm
'''
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import discord
from discord.ext import commands

# instantiate a chrome options object so you can set the size and headless preference
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--enable-javascript")
chrome_options.add_argument("user-agent=WIP")

# download the chrome driver from https://sites.google.com/a/chromium.org/chromedriver/downloads and put it in the
# current directory
chrome_driver = "./chromedriver"

# go to Google and click the I'm Feeling Lucky button
driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
driver.get("https://www.accuweather.com/en/pt/lisbon/274087/hourly-weather-forecast/274087?lang=en-us")


weather_icon_current_hour = driver.find_elements_by_xpath('//*[@id="detail-hourly"]/div/div[2]/table/tbody/tr[1]/td[1]/span')[0]
weather_icon_next_hour = driver.find_elements_by_xpath('//*[@id="detail-hourly"]/div/div[2]/table/tbody/tr[1]/td[2]/span')[0]
print(weather_icon_current_hour.text)
print(weather_icon_next_hour.text)

# capture the screen
driver.get_screenshot_as_file("capture.png")

bot = commands.Bot(command_prefix='$', description='WeatherBot')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)

@bot.command()
async def tempo():
    await bot.say('Agora está '+weather_icon_current_hour.text)
    
bot.run('NDIyODM5NTgzODc3NjI3OTA1.DYhnlA.Ax_cAy7J4KoPHbD-vjApwC_4l6c')

    
    