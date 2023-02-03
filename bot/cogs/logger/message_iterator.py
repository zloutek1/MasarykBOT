import logging
from datetime import datetime, timedelta
from typing import AsyncIterator, Optional, Union

import inject
from discord import Message, TextChannel, Thread
from discord.utils import snowflake_time
from pytz import UTC

import bot.db
from bot.utils import EmptyAsyncIterator

log = logging.getLogger(__name__)


class MessageIterator:
    _from_date: datetime
    _iterator: AsyncIterator[Message]
    _current_message: Optional[Message] = None

    @inject.autoparams('logger_repository')
    def __init__(self, channel: Union[TextChannel, Thread], logger_repository: bot.db.LoggerRepository) -> None:
        self.channel = channel
        self.logger_repository = logger_repository

    async def _get_next_from_date(self) -> datetime:
        last_process = await self.logger_repository.find_last_process(self.channel.id)
        if last_process is None:
            if self.channel.created_at is None:
                if self.channel.last_message_id is not None:
                    oldest_message = await anext(self.channel.history(oldest_first=True, limit=1))
                    return oldest_message.created_at
                else:
                    return (await self.channel.fetch_message(self.channel.id)).created_at
            else:
                return self.channel.created_at
        elif last_process.finished_at is None:
            return last_process.from_date
        else:
            return last_process.to_date

    async def history(self) -> AsyncIterator[Message]:
        from_date = min(await self._get_next_from_date(), datetime.now(tz=UTC))

        if abs(datetime.now(tz=UTC) - from_date) < timedelta(days=3):
            return EmptyAsyncIterator()

        log.info("processing messages from %s in %s (%s)", from_date.date(), self.channel.name, self.channel.guild.name)

        await self.logger_repository.begin_process((self.channel.id, from_date))
        self._iterator = aiter(self.channel.history(after=from_date, limit=1_000))
        self._from_date = from_date
        return self

    def __aiter__(self) -> "MessageIterator":
        return self

    async def __anext__(self) -> Message:
        try:
            self._current_message = await anext(self._iterator)
            return self._current_message
        except StopAsyncIteration:
            to_date = datetime.now(tz=UTC) if self._current_message is None else self._current_message.created_at
            await self.logger_repository.end_process((self.channel.id, self._from_date, to_date))
            raise StopAsyncIteration
