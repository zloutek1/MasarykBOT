import asyncio
import logging
import random
import re
from collections import Counter, defaultdict
from enum import Enum
from typing import Dict, List, Tuple, cast

from discord.ext import commands, tasks
from discord.ext.commands import has_permissions

log = logging.getLogger(__name__)

N = 2
NGram = Tuple[str, str]

SOF = "​SOF​"
EOF = "​EOF​"

class MarkovState(Enum):
    UNINITIALIZED = "UNINITIALIZED"
    READY = "READY"
    LOADING = "LOADING"
    TRAINING = "TRAINING"

class Markov(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ngrams: defaultdict[NGram] = defaultdict(dict[str, int])
        self.state = MarkovState.UNINITIALIZED

    @commands.group(invoke_without_command=True)
    async def markov(self, ctx, *message):
        if self.state != MarkovState.READY:
            return await ctx.send_error(f"markov is not ready, current state is {self.state}")

        if not self.ngrams:
            return await ctx.send_error("no data loaded")

        await ctx.send(self.to_message(self.simulate()))

    @markov.command(aliases=['retrain'])
    @has_permissions(administrator=True)
    async def train(self, ctx):
        if self.state not in (MarkovState.UNINITIALIZED, MarkovState.READY):
            return await ctx.send_error(f"markov is not ready, current state is {self.state}")

        self.state = MarkovState.TRAINING
        await ctx.send("[Training] ...")

        await self.bot.db.markov.train()

        self.state = MarkovState.UNINITIALIZED
        await ctx.reply("[Training] Finished")

    @markov.command(aliases=['reload'])
    @has_permissions(administrator=True)
    async def load(self, ctx):
        await ctx.send("[Markov] Loading data")
        if not await self._load():
            return await ctx.send_error(f"markov is not ready, current state is {self.state}")
        await ctx.reply("[Markov] Data loaded")

    @commands.Cog.listener()
    async def on_ready(self):
        self.task_reload_markov.start()

    async def _load(self):
        """
        Load markov data from database
        """
        if self.state not in (MarkovState.UNINITIALIZED, MarkovState.READY):
            return False

        log.info("Markov loading data")
        self.state = MarkovState.LOADING

        rows = await self.bot.db.markov.load()
        for row in rows:
            ngram = tuple(row.get('ngram'))
            self.ngrams[ngram][row.get('next')] = row.get('weight')

        self.state = MarkovState.READY
        log.info("Markov data loaded")
        return True

    def to_message(self, message: List[str]) -> str:
        assert message[0] == SOF
        assert message[-1] == EOF
        return " ".join(message[1:-1])

    def simulate(self) -> List[str]:
        options = [ngram
                  for ngram in self.ngrams.keys()
                  if ngram[0] == SOF]
        start = random.choice(options)

        return self.simulate_from(start)

    def simulate_from(self, ngram: NGram) -> List[str]:
        assert N == 2

        options = self.ngrams.get(ngram)
        if options is None or len(options.keys()) == 0:
            return list(ngram) + [EOF]

        following: str = random.choices(list(options.keys()), list(options.values()))[0]
        next_ngram = ngram[1:] + (following,)

        return [ngram[0]] + self.simulate_from(next_ngram)

    @tasks.loop(hours=24)
    async def task_reload_markov(self):
        log.info("Running periodic reload of markov chain")
        await self._load()

def setup(bot):
    bot.add_cog(Markov(bot))
