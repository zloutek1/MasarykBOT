import discord
import inject
from discord.ext import commands

from . import Backup
from ..history_iterator import HistoryIterator


class BotBackup(Backup[commands.Bot]):
    def __init__(self) -> None:
        super().__init__()

    async def traverse_up(self, bot: commands.Bot) -> None:
        await super().traverse_up(bot)

    async def backup(self, bot: commands.Bot) -> None:
        pass

    @inject.autoparams('guild_backup', 'message_backup')
    async def traverse_down(
        self,
        bot: commands.Bot,
        guild_backup: Backup[discord.Guild],
        message_backup: Backup[discord.Message]
    ) -> None:
        await super().traverse_down(bot)

        for guild in bot.guilds:
            await guild_backup.traverse_down(guild)

        async for week in HistoryIterator(bot):
            async for message in await week.history():
                await message_backup.traverse_down(message)
