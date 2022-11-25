import logging
from datetime import datetime, timedelta
from typing import cast, AsyncIterator

import inject
from discord import TextChannel, Message
from pytz import UTC

import bot.db
from bot.utils import EmptyAsyncIterator

log = logging.getLogger(__name__)


class MessageIterator:
    @inject.autoparams('logger_repository')
    def __init__(self, text_channel: TextChannel, logger_repository: bot.db.LoggerRepository) -> None:
        self._to_date = None
        self._from_date = None
        self._iterator = None
        self.text_channel = text_channel
        self.logger_repository = logger_repository

    async def _get_from_date(self) -> datetime:
        last_process = await self.logger_repository.find_last_process(self.text_channel.id)
        if last_process is None:
            return self.text_channel.created_at
        elif last_process['finished_at'] is None:
            return cast(datetime, last_process['from_date'])
        else:
            return cast(datetime, last_process['to_date'])

    async def history(self) -> AsyncIterator[Message]:
        from_date = min(await self._get_from_date(), datetime.now(tz=UTC))
        to_date = min(from_date + timedelta(days=7), datetime.now(tz=UTC))

        if abs(to_date - from_date) < timedelta(days=1):
            return EmptyAsyncIterator()

        log.info("backup up messages %s to %s in %s (%s)", from_date.date(), to_date.date(), self.text_channel.name,
                 self.text_channel.guild.name)

        await self.logger_repository.begin_process((self.text_channel.id, from_date, to_date))
        self._iterator = aiter(self.text_channel.history(after=from_date, before=to_date, limit=None))
        self._from_date = from_date
        self._to_date = to_date
        return self

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return await anext(self._iterator)
        except StopAsyncIteration:
            await self.logger_repository.end_process((self.text_channel.id, self._from_date, self._to_date))
            raise StopAsyncIteration
