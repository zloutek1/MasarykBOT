from collections import deque

import discord
from discord.ext import commands, tasks

from bot.cogs.markov.generation_service import MarkovGenerationService
from bot.cogs.markov.training_service import MarkovTrainingService
from bot.utils import Context, requires_database



class MarkovCog(commands.Cog):
    def __init__(
            self,
            bot: commands.Bot,
            generation_service: MarkovGenerationService = None,
            training_service: MarkovTrainingService = None
    ) -> None:
        self.bot = bot
        self.generation_service = generation_service or MarkovGenerationService()
        self.training_service = training_service or MarkovTrainingService()

        self.training_queue = deque[discord.Message]()
        self.train_message_task.start()


    @commands.group(invoke_without_command=True)
    async def markov(self, ctx: Context, *start: str) -> None:
        start = ' '.join(start)
        message = await self.generation_service.generate(ctx.guild.id, start, limit=1048)
        await ctx.reply(message or "no response")


    @markov.command(name='train', aliases=['retrain', 'grind'])
    @commands.has_permissions(administrator=True)
    async def train(self, ctx: Context) -> None:
        await self.training_service.train(ctx.guild.id)
        await ctx.reply("[markov] Finished training", mention_author=True)


    @commands.Cog.listener()
    async def on_message_backup(self, message: discord.Message) -> None:
        if self.training_service.should_learn_message(message):
            self.training_queue.append(message)


    @tasks.loop(minutes=1)
    async def train_message_task(self):
        while self.training_queue:
            message = self.training_queue.popleft()
            await self.training_service.train_message(message.guild.id, message.content)


@requires_database
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MarkovCog(bot))
