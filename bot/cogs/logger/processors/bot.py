from discord.ext import commands

from ._base import Backup

from ..history_iterator import HistoryIterator


class BotBackup(Backup[commands.Bot]):
    def __init__(self) -> None:
        super().__init__()


    async def traverse_up(self, bot: commands.Bot) -> None:
        await super().traverse_up(bot)


    async def backup(self, bot: commands.Bot) -> None:
        pass


    async def traverse_down(self, bot: commands.Bot) -> None:
        await super().traverse_down(bot)

        from .guild import GuildBackup
        for guild in bot.guilds:
            await GuildBackup().traverse_down(guild)

        from .message import MessageBackup
        async for week in HistoryIterator(bot):
            async for message in await week.history():
                await MessageBackup().traverse_down(message)
