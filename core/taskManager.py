import asyncio

from discord import Colour, Embed, Member, Object
from discord.ext import commands
from discord.ext.commands import Bot

from config import BotConfig


class TaskManager(commands.Cog):
    """No commands, just event handlers."""

    def __init__(self, bot: Bot):
        self.bot = bot

        self.tasklist = {}  # every_seconds: [tasks]
        self.bot.add_background_task = self.add_background_task

    async def runTaskEvery(self, seconds: int):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            # do stuff
            for task in self.tasklist[seconds]:
                await task()

            await asyncio.sleep(seconds)

    def add_background_task(self, task, repeat_every: int = 60):
        assert repeat_every % 5 == 0, "time has to be divisible by 5"

        if repeat_every in self.tasklist:
            self.tasklist[repeat_every].append(task)

        else:
            self.tasklist[repeat_every] = [task]
            self.bot.loop.create_task(self.runTaskEvery(seconds=repeat_every))


def setup(bot):
    bot.add_cog(TaskManager(bot))
    print("Cog loaded: TaskManager")
