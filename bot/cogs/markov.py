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
from redis import Redis
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

def to_thread(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper

class Markov(commands.Cog):
    messageDao = MessageDao()
    redis = cast(Redis[str], inject.attr('redis'))

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.state = MarkovState.UNINITIALIZED
        self.possible_starts: List[NGram] = []


    @commands.group(invoke_without_command=True)
    async def markov(self, ctx: Context, *_anything: str) -> None:
        if self.state != MarkovState.READY:
            await ctx.send_error(f"markov is not ready, current state is {self.state}")
            return

        i = 0
        while i < 100:
            state = self.simulate()
            if len(state) <= 2:
                i += 2
            else:
                break
        else:
            await ctx.send_error(f"markov chain simulation timed out :(")
            return

        await ctx.reply(escape_mentions(self.to_message(state)))

    @markov.command(aliases=['retrain'])
    @has_permissions(administrator=True)
    async def train(self, ctx: Context) -> None:
        await ctx.send("[Markov] Training ...")

        success = await self._train()
        if not success:
            await ctx.send_error(f"markov is not ready, current state is {self.state}")
            return

        await ctx.reply("[Markov] Finished training")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        messages = await self.messageDao.select_all_long()

        self.possible_starts = []
        for message in messages:
            next = cast(str, message['content']).split(maxsplit=1)[0]
            self.possible_starts.append((SOF, next))

        self.state = MarkovState.READY

    def to_message(self, parts: List[str]) -> str:
        assert parts[0] == SOF, f"message parts must start with SOF, but was {parts}"
        assert parts[-1] == EOF, f"message parts must end with EOF, but was {parts}"
        return " ".join(parts[1:-1])

    def simulate(self) -> List[str]:
        start = random.choice(self.possible_starts)
        return self.simulate_from(start)

    def simulate_from(self, ngram: NGram) -> List[str]:
        assert N == 2, "ERROR: expected Ngram size 2"

        options = self.redis.json().get("markov." + SEP.join(ngram))
        if options is None or len(options.keys()) == 0:
            return [EOF]

        following: str = random.choices(list(options.keys()), list(options.values()))[0]
        next_ngram = ngram[1:] + (following,)

        return [ngram[0]] + self.simulate_from(next_ngram)

    async def _train(self) -> bool:
        if self.state not in (MarkovState.UNINITIALIZED, MarkovState.READY):
            return False

        self.state = MarkovState.TRAINING
        log.info("Markov training started")

        messages = await self.messageDao.select_all_long()
        for i, message in enumerate(messages):
            percentage = int((i + 1) / len(messages) * 100)
            if int((i) / len(messages) * 100) < percentage:
                log.info(f"Training at {percentage}%")

            if len(message['content'].strip()) == 0:
                continue

            line = f"{SOF} {message['content']} {EOF}"
            await self.markov_train_line(message, line)

        log.info("Markov training finished")
        self.state = MarkovState.UNINITIALIZED
        return True

    @to_thread
    def markov_train_line(self, message: Record, line: str) -> None:
        words = line.split()
        words = [word for word in words if self.filter_word(message, word)]
        if not words:
            return

        for i in range(len(words) - N):
            ngram = words[i:i+N]
            next = words[i+N]

            options = self.redis.json().get("markov." + SEP.join(ngram)) or {}
            options[next] = options.get(next, 0) + 1
            self.redis.json().set("markov." + SEP.join(ngram), Path.rootPath(), options)

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
