import asyncio

from discord import Colour, Embed, Member, Object
from discord.ext import commands
from discord.ext.commands import Bot

from config import BotConfig


class TaskManager(commands.Cog):
    """No commands, just event handlers."""

    def __init__(self, bot: Bot):
        self.bot = bot

        self.tasklist = {60: []}
        self.bot.add_background_task = self.add_background_task

        self.bot.loop.create_task(self.oneMinuteTasks())

    async def oneMinuteTasks(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            # do stuff
            for task in self.tasklist[60]:
                await task()

            await asyncio.sleep(60)

    def add_background_task(self, task, timer=60):
        self.tasklist[timer].append(task)


def setup(bot):
    bot.add_cog(TaskManager(bot))
    print("Cog loaded: TaskManager")
