import logging

import discord
import inject
from discord.utils import get

from bot.constants import CONFIG
from bot.db import MessageRepository, UnitOfWork
from bot.db.cogs import MarkovEntity, MarkovRepository
from bot.utils.progress import ProgressReporter

log = logging.getLogger(__name__)

DEFAULT_CONTEXT_SIZE = 8


class MarkovTrainingService:
    @inject.autoparams('message_repository', 'markov_repository', 'uow')
    def __init__(self, message_repository: MessageRepository, markov_repository: MarkovRepository,
                 uow: UnitOfWork) -> None:
        self.message_repository = message_repository
        self.markov_repository = markov_repository
        self.uow = uow

    @staticmethod
    def should_learn_message(message: discord.Message) -> bool:
        return (
            not message.author.bot and
            not message.content.startswith(('!', 'pls')) and
            message.guild is not None
        )

    async def train(self, guild_id: int) -> None:
        await self.markov_repository.truncate()

        progress = ProgressReporter(
            max_count=await self.message_repository.count(),
            report_percentage=1,
            message="markov training progress %d%%"
        )

        log.info("training in guild %d started", guild_id)
        async with self.uow.transaction(readonly=True) as transaction:
            paginator = await self.markov_repository.find_training_messages(guild_id, conn=transaction.conn)
            async for messages in paginator:
                for message in messages:
                    await self.train_message(guild_id, message.content)
                    progress.increment()
        log.info("training in guild %d finished", guild_id)

    async def train_message(self, guild_id: int, message: str) -> None:
        context_size = self._get_context_size(guild_id)
        async with self.uow.transaction() as transaction:
            for i in range(len(message)):
                context = message[max(0, i - context_size):i]
                follows = message[i]

                entity = MarkovEntity(guild_id, context, follows)
                await self.markov_repository.insert(entity, conn=transaction.conn)

    @staticmethod
    def _get_context_size(guild_id: int) -> int:
        if not (guild_config := get(CONFIG.guilds, id=guild_id)):
            return DEFAULT_CONTEXT_SIZE
        if not (markov_config := guild_config.cogs.markov):
            return DEFAULT_CONTEXT_SIZE
        return markov_config.context_size
