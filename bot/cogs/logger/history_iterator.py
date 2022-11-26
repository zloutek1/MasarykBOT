import logging

import inject
from discord import TextChannel
from discord.ext import commands

import bot.db
from bot.db import Record
from .message_iterator import MessageIterator

log = logging.getLogger(__name__)


class HistoryIterator:
    @inject.autoparams('logger_repository')
    def __init__(self, bot: commands.Bot, logger_repository: bot.db.LoggerRepository) -> None:
        self.bot = bot
        self.logger_repository = logger_repository
        self.updatable_processes: list[Record] = []

    def __aiter__(self) -> "HistoryIterator":
        return self

    async def __anext__(self) -> "MessageIterator":
        if not self.updatable_processes:
            self.updatable_processes = await self.logger_repository.find_updatable_processes()

        if not self.updatable_processes:
            raise StopAsyncIteration

        log.info('starting message processors batch')
        process = self.updatable_processes.pop()
        channel = await self.bot.fetch_channel(process['channel_id'])
        assert isinstance(channel, TextChannel)
        return MessageIterator(channel)
