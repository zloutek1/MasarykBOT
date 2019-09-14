from discord import Game
from discord.ext.commands import when_mentioned_or

from core.bot import MasarykBot

import os
from glob import glob
import time
import json
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    print()

    bot = MasarykBot(
        command_prefix=when_mentioned_or(os.getenv("PREFIX")),
        case_insensitive=True
    )

    with open("assets/loaded_cogs.json", "r") as fileR:
        modules = json.load(fileR)

    ##
    # print boot message
    ##
    boot_message = """
    Boot sequence initialised

    Seeking cogs...
    {} cogs found

    Loading cogs...""".format(len(modules))
    for letter in boot_message.strip("\n"):
        print(letter, end="")
    print()

    ##
    # load cogs
    ##
    for module in modules:
        bot.load_extension(module)
    print("    Loaded:", ", ".join(bot.cogs.keys()) or "No cogs found")
    print()

    ##
    # start bot
    ##
    bot.start(os.getenv("TOKEN"))
