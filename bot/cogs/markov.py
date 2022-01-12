import asyncio
import logging
import math
import random
import re
from collections import Counter, defaultdict
from enum import Enum
from typing import Dict, List, Tuple, cast

from discord.ext import commands, tasks
from discord.ext.commands import has_permissions
from discord.utils import escape_mentions
from redis.commands.json.path import Path

log = logging.getLogger(__name__)

N = 2
NGram = Tuple[str, str]

SOF = "​SOF​"
EOF = "​EOF​"
SEP = "​,​"

class MarkovState(Enum):
    UNINITIALIZED = "UNINITIALIZED"
    READY = "READY"
    TRAINING = "TRAINING"

class Markov(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.state = MarkovState.UNINITIALIZED

        assert self.bot.redis is not None, "this cog requires redis to function"

    @commands.group(invoke_without_command=True)
    async def markov(self, ctx, *_anything):
        if self.state != MarkovState.READY:
            return await ctx.send_error(f"markov is not ready, current state is {self.state}")

        message = self.to_message(self.simulate())
        await ctx.reply(escape_mentions(message), mention_author=False)

    @markov.command(aliases=['retrain'])
    @has_permissions(administrator=True)
    async def train(self, ctx):
        await ctx.send("[Markov] Training ...")
        if not await self._train():
            return await ctx.send_error(f"markov is not ready, current state is {self.state}")
        await ctx.reply("[Markov] Finished training")

    @commands.Cog.listener()
    async def on_ready(self):
        await self._train()

    def to_message(self, message: List[str]) -> str:
        assert message[0] == SOF
        assert message[-1] == EOF
        return " ".join(message[1:-1])

    def simulate(self) -> List[str]:
        possible_starts = [
            key
            for key in self.bot.redis.scan_iter("markov.*")
            if key.startswith("markov." + SOF)]
        start = random.choice(possible_starts)

        ngram = cast(NGram, tuple(start.lstrip("markov.").split(SEP)))
        return self.simulate_from(ngram)

    def simulate_from(self, ngram: NGram) -> List[str]:
        assert N == 2

        options = self.bot.redis.json().get("markov." + SEP.join(ngram))
        if options is None or len(options.keys()) == 0:
            return [EOF]

        following: str = random.choices(list(options.keys()), list(options.values()))[0]
        next_ngram = ngram[1:] + (following,)

        return [ngram[0]] + self.simulate_from(next_ngram)

    async def _train(self):
        if self.state not in (MarkovState.UNINITIALIZED, MarkovState.READY):
            return False
        self.state = MarkovState.TRAINING

        messages = await self.bot.db.messages.select_all_long()
        for i, message in enumerate(messages):
            percentage = int((i + 1) / len(messages) * 100)
            if int((i) / len(messages) * 100) < percentage:
                log.info(f"Training at {percentage}%")

            if len(message.get('content').strip()) == 0:
                continue

            line = f"{SOF} {message.get('content')} {EOF}"
            self.markov_train_line(message, line)

        self.state = MarkovState.UNINITIALIZED

    def markov_train_line(self, message, line: str):
        words = line.split()
        words = [word for word in words if self.filter_word(message, word)]
        if not words:
            return

        for i in range(len(words) - N):
            ngram = words[i:i+N]
            next = words[i+N]

            options = self.bot.redis.json().get("markov." + SEP.join(ngram)) or {}
            options[next] = options.get(next, 0) + 1
            self.bot.redis.json().set("markov." + SEP.join(ngram), Path.rootPath(), options)

    def filter_word(self, message, word: str):
        author = self.bot.get_user(message.get('author_id'))
        return not (
            any(word.startswith(prefix) for prefix in ['!', 'pls']) or
            word.startswith("@") or
            "<@" in word or
            "<!@" in word or
            "<:@" in word or
            author.bot if author else False
        )

def setup(bot):
    bot.add_cog(Markov(bot))
