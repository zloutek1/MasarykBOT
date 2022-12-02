import logging

import discord
import inject

from bot.db import MessageRepository, UnitOfWork
from bot.db.cogs import MarkovEntity, MarkovRepository
from bot.utils.progress import ProgressReporter

log = logging.getLogger(__name__)

CONTEXT_SIZE = 8



class MarkovTrainingService:
    @inject.autoparams('message_repository', 'markov_repository', 'uow')
    def __init__(self, message_repository: MessageRepository, markov_repository: MarkovRepository, uow: UnitOfWork) -> None:
        self.message_repository = message_repository
        self.markov_repository = markov_repository
        self.uow = uow


    @staticmethod
    def can_learn_message(message: discord.Message) -> bool:
        return not message.author.bot


    async def train(self, guild_id: int) -> None:
        await self.markov_repository.truncate()

        progress = ProgressReporter(
            max_count=await self.message_repository.count(),
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
        async with self.uow.transaction() as transaction:
            for i in range(len(message)):
                context = message[max(0, i - CONTEXT_SIZE):i]
                follows = message[i]

                entity = MarkovEntity(guild_id, context, follows)
                await self.markov_repository.insert(entity, conn=transaction.conn)
