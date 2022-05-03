import asyncio
import functools
import logging
import random
from enum import Enum
from typing import Any, Callable, List, Tuple, cast

import inject
from bot.cogs.utils.context import Context
from bot.db.messages import MessageDao
from bot.db.utils import Record
from disnake.ext import commands
from disnake.ext.commands import has_permissions
from disnake.utils import escape_mentions
from aioredis import Redis

log = logging.getLogger(__name__)

N = 2
NGram = Tuple[str, str]

SOF = "​SOF​"
EOF = "​EOF​"
SEP = "​.​"

class MarkovState(Enum):
    UNINITIALIZED = "UNINITIALIZED"
    READY = "READY"
    TRAINING = "TRAINING"

class Markov(commands.Cog):
    messageDao = MessageDao()
    redis = inject.attr(Redis)

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.state = MarkovState.UNINITIALIZED
        self.possible_starts: List[NGram] = []
        self.training_progress = 100

    @commands.group(invoke_without_command=True)
    async def markov(self, ctx: Context, *_anything: str) -> None:
        if self.state != MarkovState.READY:
            if self.state == MarkovState.TRAINING:
                await ctx.send_error(f"markov is not ready, current state is {self.state}. Current progress {self.training_progress}%")
            else:
                await ctx.send_error(f"markov is not ready, current state is {self.state}")
            return

        if not self.possible_starts:
            await ctx.send_error("no possible starts")
            return
            
        state = await self.simulate()

        await ctx.reply(escape_mentions(self.to_message(state)))

    @markov.command(name='train', aliases=['retrain', 'grind'])
    @has_permissions(administrator=True)
    async def _train(self, ctx: Context) -> None:
        await ctx.send("[Markov] Grinding ...")

        success = await self.train()
        if not success:
            await ctx.send_error(f"markov is not ready, current state is {self.state}")
            return

        await ctx.reply("[Markov] Finished grinding")
        await self.load()

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self.load()

    @markov.command(name="load")
    @has_permissions(administrator=True)
    async def _load(self, ctx) -> None:
        await self.load()

    async def load(self) -> None:
        log.info("loading markov messages")
        
        self.possible_starts = []
        async for key in self.redis.scan_iter(match="markov." + SOF + SEP + "*"):
            ngram = tuple(key.lstrip("markov.").split(SEP, 1))
            self.possible_starts.append(ngram)
        
        else:
            self.state = MarkovState.READY
            log.info(f"loaded {len(self.possible_starts)} markov starts")

    def to_message(self, parts: List[str]) -> str:
        assert parts[0] == SOF, f"message parts must start with SOF, but was {parts}"
        assert parts[-1] == EOF, f"message parts must end with EOF, but was {parts}"
        return " ".join(parts[1:-1])

    async def simulate(self) -> List[str]:
        start = random.choice(self.possible_starts)
        return await self.simulate_from(start)

    async def simulate_from(self, ngram: NGram) -> List[str]:
        assert N == 2, "ERROR: expected Ngram size 2"

        options = await self.redis.hgetall("markov." + SEP.join(ngram))
        if options is None or len(options.keys()) == 0:
            return [EOF]

        possible_nexts = list(options.keys())
        weights = [int(weight) for weight in options.values()]

        following: str = random.choices(possible_nexts, weights)[0]
        next_ngram = ngram[1:] + (following,)

        return [ngram[0]] + await self.simulate_from(next_ngram)

    async def train(self) -> bool:
        if self.state not in (MarkovState.UNINITIALIZED, MarkovState.READY):
            return False

        self.state = MarkovState.TRAINING
        log.info("Markov training started")
        self.training_progress = 0

        await self.redis.flushall()
        
        messages = await self.messageDao.select_all_long()
        for i, message in enumerate(messages):
            percentage = int((i + 1) / len(messages) * 100)
            if int((i) / len(messages) * 100) < percentage:
                log.info(f"Training at {percentage}%")
                self.training_progress = percentage

            if len(message['content'].strip()) == 0:
                continue

            line = f"{SOF} {message['content']} {EOF}"
            await self.markov_train_line(message, line)

        log.info("Markov training finished")
        self.state = MarkovState.UNINITIALIZED
        return True

    async def markov_train_line(self, message: Record, line: str) -> None:
        words = line.split()
        words = [word for word in words if self.filter_word(message, word)]
        if not words:
            return

        for i in range(len(words) - N):
            ngram = words[i:i+N]
            next = words[i+N]

            options = await self.redis.hgetall("markov." + SEP.join(ngram)) or {}
            options[next] = int(options.get(next, 0)) + 1
            await self.redis.hset("markov." + SEP.join(ngram), mapping=options)

    def filter_word(self, message: Record, word: str) -> bool:
        author = self.bot.get_user(message['author_id'])
        return not (
            any(word.startswith(prefix) for prefix in ['!', 'pls']) or
            word.startswith("@") or
            "<@" in word or
            "<!@" in word or
            "<:@" in word or
            author.bot if author else False
        )

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Markov(bot))
