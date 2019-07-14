
from discord import Game
from discord.ext.commands import Bot, when_mentioned_or

import config as BotConfig


bot = Bot(
    command_prefix=when_mentioned_or(BotConfig.prefix),
    activity=Game(name="Commands: !help"),
    case_insensitive=True
)

# Internal/debug
bot.load_extension("bot.cogs.events")

bot.run(TOKEN)
bot.http_session.close()  # Close the aiohttp session when the bot finishes running
