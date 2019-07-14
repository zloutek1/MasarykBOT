import discord
from discord.ext import commands
from config import *

bot = commands.Bot(command_prefix=PREFIX, pm_help=None, description='A bot that does stuff.... probably')


bot.run(TOKEN)
