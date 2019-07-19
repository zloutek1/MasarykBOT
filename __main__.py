from discord import Game
from discord.ext.commands import when_mentioned_or

from core.bot import MasarykBot
from config import BotConfig

bot = MasarykBot(
    command_prefix=when_mentioned_or(BotConfig.prefix),
    activity=Game(name="Commands: !help"),
    case_insensitive=True,
    db_config=BotConfig.db_config
)

# Internal/debug
bot.load_extension("core.events")
bot.load_extension("core.taskManager")
bot.load_extension("core.errors")
bot.load_extension("core.admin")

# Commands
bot.load_extension("cogs.picker")
bot.load_extension("cogs.antispam")


bot.start(BotConfig.token)
