import logging
from collections.abc import AsyncIterator
from typing import Optional

import discord.errors
import inject
from discord import TextChannel
from discord.ext import commands

import bot.db
from bot.db import LoggerRepository, ChannelRepository
from .message_iterator import MessageIterator

log = logging.getLogger(__name__)



class HistoryIterator(AsyncIterator[MessageIterator]):
    @inject.autoparams('logger_repository', 'channel_repository')
    def __init__(self, bot: commands.Bot, logger_repository: LoggerRepository,
                 channel_repository: ChannelRepository) -> None:
        self.bot = bot
        self._logger_repository = logger_repository
        self._channel_repository = channel_repository
        self.updatable_processes: list[LoggerRepository.UpdatableProcesses] = []


    def __aiter__(self) -> "HistoryIterator":
        return self


    async def __anext__(self) -> "MessageIterator":
        if not self.updatable_processes:
            log.info('starting message processors batch')
            self.updatable_processes = await self._logger_repository.find_updatable_processes()

        channel: Optional[TextChannel] = None
        while not channel:
            channel = await self.get_next_channel_to_process()

        return MessageIterator(channel)


    async def get_next_channel_to_process(self) -> Optional[TextChannel]:
        if not self.updatable_processes:
            raise StopAsyncIteration

        process = self.updatable_processes.pop()
        try:
            channel = await self.bot.fetch_channel(process.channel_id)
            assert isinstance(channel, TextChannel)
            return channel
        except discord.NotFound:
            log.info(f"Channel {process.channel_id} not longer exists, marking as deleted")
            await self.mark_channel_as_deleted(process.channel_id)
            return None


    async def mark_channel_as_deleted(self, channel_id: int) -> None:
        await self._channel_repository.soft_delete([(channel_id,)])
