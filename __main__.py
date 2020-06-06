from discord.ext.commands import when_mentioned_or

from core.bot import MasarykBot

import os
import json
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()

    bot = MasarykBot(
        command_prefix=when_mentioned_or(os.getenv("PREFIX")),
        case_insensitive=True
    )

    # load cogs
    with open("assets/loaded_cogs.json", "r") as fileR:
        modules = json.load(fileR)

        for module in modules:
            bot.load_extension(module)

    # start bot
    bot.start(os.getenv("TOKEN"))
