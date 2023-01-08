import logging
from datetime import datetime, timedelta
from typing import AsyncIterator, Optional

import inject
from discord import TextChannel, Message
from discord.utils import snowflake_time
from pytz import UTC

import bot.db
from bot.utils import EmptyAsyncIterator

log = logging.getLogger(__name__)



class MessageIterator:
    _to_date: datetime
    _from_date: datetime
    _iterator: AsyncIterator[Message]


    @inject.autoparams('logger_repository')
    def __init__(self, text_channel: TextChannel, logger_repository: bot.db.LoggerRepository) -> None:
        self.text_channel = text_channel
        self.logger_repository = logger_repository


    async def _get_from_date(self) -> datetime:
        last_process = await self.logger_repository.find_last_process(self.text_channel.id)
        if last_process is None:
            return self.text_channel.created_at
        elif last_process.finished_at is None:
            return last_process.from_date
        else:
            return last_process.to_date


    async def history(self) -> AsyncIterator[Message]:
        from_date = min(await self._get_from_date(), datetime.now(tz=UTC))
        to_date = min(from_date + timedelta(days=7), datetime.now(tz=UTC))

        if abs(to_date - from_date) < timedelta(days=1):
            return EmptyAsyncIterator()

        if res := await self._try_to_skip_empty_channel(from_date, to_date):
            return res

        if res := await self._try_to_skip_after_last_message(from_date, to_date):
            return res

        log.info("processing messages from %s to %s in %s (%s)", from_date.date(), to_date.date(), self.text_channel.name,
                 self.text_channel.guild.name)

        await self.logger_repository.begin_process((self.text_channel.id, from_date, to_date))
        self._iterator = aiter(self.text_channel.history(after=from_date, before=to_date, limit=None))
        self._from_date = from_date
        self._to_date = to_date
        return self

    async def _try_to_skip_empty_channel(self, from_date: datetime, to_date: datetime) -> Optional[AsyncIterator[Message]]:
        if self.text_channel.last_message_id is None:
            new_to_date = datetime.now(tz=UTC) - timedelta(days=2)
            if to_date >= new_to_date:
                return None
            await self.logger_repository.insert_process((self.text_channel.id, from_date, new_to_date))
            log.info("skipping forward messages in empty channel from %s to %s in %s (%s)", from_date.date(), new_to_date.date(),
                     self.text_channel.name, self.text_channel.guild.name)
            return EmptyAsyncIterator()
        return None

    async def _try_to_skip_after_last_message(self, from_date: datetime, to_date: datetime) -> Optional[AsyncIterator[Message]]:
        if self.text_channel.last_message_id is not None:
            last_message_sent_at = snowflake_time(self.text_channel.last_message_id)
            if from_date < last_message_sent_at:
                return None

            new_to_date = datetime.now(tz=UTC) - timedelta(days=2)
            if to_date >= new_to_date:
                return None

            log.info("skipping forward messages from %s to %s in %s (%s)", from_date.date(), new_to_date.date(),
                     self.text_channel.name, self.text_channel.guild.name)
            await self.logger_repository.insert_process((self.text_channel.id, from_date, new_to_date))
            return EmptyAsyncIterator()
        return None

    def __aiter__(self) -> "MessageIterator":
        return self


    async def __anext__(self) -> Message:
        try:
            return await anext(self._iterator)
        except StopAsyncIteration:
            await self.logger_repository.end_process((self.text_channel.id, self._from_date, self._to_date))
            raise StopAsyncIteration
