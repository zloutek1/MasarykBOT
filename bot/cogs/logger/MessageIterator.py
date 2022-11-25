import logging
from datetime import datetime, timedelta
from typing import cast, AsyncIterator

import inject
from discord import TextChannel, Message

import bot.db

log = logging.getLogger(__name__)


class MessageIterator:
    @inject.autoparams('logger_repository')
    def __init__(self, text_channel: TextChannel, logger_repository: bot.db.LoggerRepository) -> None:
        self.text_channel = text_channel
        self.logger_repository = logger_repository

    async def _get_from_date(self) -> datetime:
        last_process = await self.logger_repository.find_last_process(self.text_channel.id)
        if last_process is None:
            return self.text_channel.created_at
        else:
            return cast(datetime, last_process['to_date'])

    async def history(self) -> AsyncIterator[Message]:
        from_date = await self._get_from_date()
        to_date = min(from_date + timedelta(days=7), datetime.now())
        log.info("backup up messages %s to %s in %s (%s)", from_date.date(), to_date.date(), self.text_channel.name,
                 self.text_channel.guild.name)

        async with self.logger_repository.with_process((self.text_channel.id, from_date, to_date)):
            return self.text_channel.history(after=from_date, before=to_date, limit=None)
