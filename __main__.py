from discord import Game
from discord.ext.commands import when_mentioned_or

from core.bot import MasarykBot
from config import BotConfig

if __name__ == "__main__":
    bot = MasarykBot(
        command_prefix=when_mentioned_or(BotConfig.prefix),
        activity=Game(name="Commands: !help"),
        case_insensitive=True,
        db_config=BotConfig.db_config
    )

    # Internal/debug
    print("---[ Internal ]---")
    bot.load_extension("core.events")
    bot.load_extension("core.taskManager")
    # bot.load_extension("core.errors")
    bot.load_extension("core.admin")

    # Commands
    print("\n---[ Commands ]---")
    bot.load_extension("cogs.reactionPicker")
    bot.load_extension("cogs.antispam")
    bot.load_extension("cogs.backup")

    bot.start(BotConfig.token)
