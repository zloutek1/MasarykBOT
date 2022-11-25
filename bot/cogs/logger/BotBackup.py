from discord.ext import commands

from bot.cogs.logger.Backup import Backup


class BotBackup(Backup[commands.Bot]):
    async def traverseUp(self, bot: commands.Bot) -> None:
        await super().traverseUp(bot)


    async def backup(self, bot: commands.Bot) -> None:
        pass


    async def traverseDown(self, bot: commands.Bot) -> None:
        await super().traverseDown(bot)

        from .GuildBackup import GuildBackup
        for guild in bot.guilds:
            await GuildBackup().traverseDown(guild)

        """
        from .GuildBackup import GuildBackup
        from .HistoryIterator import HistoryIterator
        from .MessageBackup import MessageBackup
        await super().traverseDown(bot)
        
        for guild in bot.guilds:
            await GuildBackup().traverseDown(guild)

        async for week in await HistoryIterator(bot).iter():
            async for message in await week.history():
                await MessageBackup().traverseDown(message)
        """