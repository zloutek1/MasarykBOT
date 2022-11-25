import inject
from discord import TextChannel
from discord.ext import commands

import bot.db
from bot.db import Record
from .MessageIterator import MessageIterator


class HistoryIterator:
    @inject.autoparams('logger_repository')
    def __init__(self, bot: commands.Bot, logger_repository: bot.db.LoggerRepository) -> None:
        self.bot = bot
        self.logger_repository = logger_repository
        self.updatable_processes: list[Record] = []

    async def iter(self) -> "HistoryIterator":
        self.updatable_processes = await self.logger_repository.find_updatable_processes()
        return self

    def __aiter__(self) -> "HistoryIterator":
        return self

    async def __anext__(self) -> "MessageIterator":
        if not self.updatable_processes:
            raise StopAsyncIteration
        process = self.updatable_processes.pop()
        channel = await self.bot.fetch_channel(process['channel_id'])
        assert isinstance(channel, TextChannel)
        return MessageIterator(channel)  # type: ignore[no-any-return]
