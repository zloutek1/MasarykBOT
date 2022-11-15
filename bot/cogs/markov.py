import logging
import random
from typing import TYPE_CHECKING, Dict, List, Tuple, cast

import inject
from aioredis import Redis
from discord.ext import commands
from discord.utils import escape_mentions

from bot.cogs.utils.context import Context
from bot.db import MessageDao

if TYPE_CHECKING:
    from bot.bot import MasarykBOT


log = logging.getLogger(__name__)

N = 2
NGram = Tuple[str, str]

SOF = "​SOF​"
EOF = "​EOF​"
SEP = "​.​"



class MarkovTrainService:
    @inject.autoparams('messageDao', 'redis')
    def __init__(self, messageDao: MessageDao, redis: Redis) -> None:
        self.messageDao = messageDao
        self.redis = redis


    async def train(self) -> None:
        await self.clear_cache()

        messages = await self.messageDao.find_all_longer_then(10)
        for message in messages:
            await self.markov_train_line(message['content'])
                

    async def clear_cache(self) -> None:
        await self.redis.flushall()


    async def markov_train_line(self, line: str) -> None:
        line = f"{SOF} {line} {EOF}"
        words = line.split()
        for i in range(len(words) - N):
            await self._increment_entry(
                ngram=cast(NGram, tuple(words[i:i+N])), 
                next=words[i+N]
            )


    async def _increment_entry(self, ngram: NGram, next: str) -> None:
        key = "markov." + SEP.join(ngram)
        options: Dict[str, str] = await self.redis.hgetall(key) or {}
        options[next] = str(int(options.get(next, 0)) + 1)
        await self.redis.hset(key, mapping=options)



class MarkovGenerateService:
    @inject.autoparams('redis')
    def __init__(self, redis: Redis) -> None:
        self.redis = redis
        self.possible_starts: set[NGram] = set()


    async def load(self) -> None:
        self.possible_starts = set()
        async for key in self.redis.scan_iter(match=f"markov.{SOF}{SEP}*"):
            key = cast(str, key)
            ngram = cast(NGram, tuple(key.lstrip("markov.").split(SEP)))
            self.possible_starts.add(ngram)
        log.info(f"loaded {len(self.possible_starts)} possible starts")


    async def generate_message(self) -> str:
        counter = 0
        message = ""
        while len(message) == 0 and counter < 1_000:
            message = await self._generate_message()
            counter += 1
        return message


    async def _generate_message(self) -> str:
        start = random.choice(tuple(self.possible_starts))

        state = await self.simulate_from(start)
        message = self.to_message(state)

        return message


    async def simulate_from(self, ngram: NGram) -> List[str]:
        assert N == 2, "ERROR: expected Ngram size 2"

        options: Dict[str, str] = await self.redis.hgetall("markov." + SEP.join(ngram)) or {}
        if len(options.keys()) == 0:
            return [EOF]

        possible_nexts = list(options.keys())
        weights = [int(weight) for weight in options.values()]

        following: str = random.choices(possible_nexts, weights)[0]
        next_ngram: NGram = ngram[1:] + (following,)

        return [ngram[0]] + await self.simulate_from(next_ngram)


    @staticmethod
    def to_message(parts: List[str]) -> str:
        assert parts[0] == SOF, f"message parts must start with SOF, but was {parts}"
        assert parts[-1] == EOF, f"message parts must end with EOF, but was {parts}"
        return " ".join(parts[1:-1])



class MarkovService(MarkovTrainService, MarkovGenerateService):
    def __init__(self) -> None:
        super(MarkovTrainService, self).__init__()
        super(MarkovGenerateService, self).__init__()



class Markov(commands.Cog):
    def __init__(self, bot: commands.Bot, service: MarkovService = None) -> None:
        self.bot = bot
        self.service = service or MarkovService()


    @commands.group(invoke_without_command=True)
    async def markov(self, ctx: Context, *_anything: str) -> None:
        try:
            message = await self.service.generate_message()
            message = escape_mentions(message)
            await ctx.reply(message or "no message")
        except Exception as ex:
            await ctx.send_error(str(ex))


    @markov.command(name='train', aliases=['retrain', 'grind'])
    @commands.has_permissions(administrator=True)
    async def train(self, ctx: Context) -> None:
        await ctx.send("[Markov] Grinding ...")

        await self.service.train()
        
        await ctx.reply("[Markov] Finished grinding")


    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self.service.load()


    @markov.command(name="load")
    @commands.has_permissions(administrator=True)
    async def load(self, ctx: Context) -> None:
        await self.service.load()

    

async def setup(bot: "MasarykBOT") -> None:
    await bot.add_cog(Markov(bot))
