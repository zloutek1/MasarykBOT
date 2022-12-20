import logging
from collections import deque
from typing import Optional, cast

import discord
from discord.ext import commands, tasks

from bot.cogs.markov.generation_service import MarkovGenerationService
from bot.cogs.markov.training_service import MarkovTrainingService
from bot.utils import Context, requires_database
from bot.utils.extra_types import GuildContext, GuildMessage

log = logging.getLogger(__name__)



class MarkovCog(commands.Cog):
    def __init__(
            self,
            bot: commands.Bot,
            generation_service: Optional[MarkovGenerationService] = None,
            training_service: Optional[MarkovTrainingService] = None
    ) -> None:
        self.bot = bot
        self.generation_service = generation_service or MarkovGenerationService()
        self.training_service = training_service or MarkovTrainingService()

        self.training_queue = deque[GuildMessage]()
        self.train_message_task.start()


    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def markov(self, ctx: GuildContext, *start_of_message: str) -> None:
        start = ' '.join(start_of_message)
        async with ctx.typing(ephemeral=True):
            message = await self.generation_service.generate(ctx.guild.id, start, limit=1048)
            await ctx.reply(message or "no response")
        log.debug("generated markov message %s", message or "no response")


    @markov.command(name='train', aliases=['retrain', 'grind'])
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def train(self, ctx: GuildContext) -> None:
        await self.training_service.train(ctx.guild.id)
        await ctx.reply("[markov] Finished training", mention_author=True)


    @commands.Cog.listener()
    async def on_message_backup(self, message: discord.Message) -> None:
        if self.training_service.should_learn_message(message):
            self.training_queue.append(cast(GuildMessage, message))


    @tasks.loop(minutes=1)
    async def train_message_task(self) -> None:
        while self.training_queue:
            message = self.training_queue.popleft()
            await self.training_service.train_message(message.guild.id, message.content)


    async def markov_from_message(self, message: discord.Message) -> bool:
        ctx = await self.bot.get_context(message)
        if ctx.command or not self.bot.user or self.bot.user not in message.mentions:
            return False

        start = ctx.message.content.split(' ')
        if self.bot.user.mention == start[0]:
            start.pop(0)

        print("markov", start)
        await self.markov(ctx, *start)
        return True


@requires_database
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MarkovCog(bot))
