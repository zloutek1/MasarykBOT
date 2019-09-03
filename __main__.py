from discord import Game
from discord.ext.commands import when_mentioned_or

from core.bot import MasarykBot
from config import BotConfig

from glob import glob
import time


if __name__ == "__main__":
    print()

    bot = MasarykBot(
        command_prefix=when_mentioned_or(BotConfig.prefix),
        case_insensitive=True
    )

    modules = [
        "core.logger",
        "core.events",
        "core.admin",
        "core.rules",
        "core.help",

        "cogs.leaderboard",
        "cogs.fun",
        "cogs.reactionmenu",
        "cogs.aboutmenu",
        "cogs.math"
    ]

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
    bot.start(BotConfig.token)
