from discord.ext import commands

from bot.cogs.logger.Backup import Backup
from bot.cogs.logger.HistoryIterator import HistoryIterator
from bot.cogs.logger.MessageBackup import MessageBackup


class BotBackup(Backup[commands.Bot]):
    async def traverse_up(self, bot: commands.Bot) -> None:
        await super().traverse_up(bot)

    async def backup(self, bot: commands.Bot) -> None:
        pass

    async def traverse_down(self, bot: commands.Bot) -> None:
        await super().traverse_down(bot)

        from .GuildBackup import GuildBackup
        for guild in bot.guilds:
            await GuildBackup().traverse_down(guild)

        async for week in HistoryIterator(bot):
            async for message in await week.history():
                await MessageBackup().traverse_down(message)
