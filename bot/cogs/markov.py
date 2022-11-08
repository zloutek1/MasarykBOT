import logging
from enum import Enum
from typing import TYPE_CHECKING, Dict, Tuple
import inject

from discord.ext import commands
from discord.ext.commands import has_permissions
from aioredis import Redis

from bot.cogs.utils.context import Context
from bot.db.messages import MessageDao

if TYPE_CHECKING:
    from bot.bot import MasarykBOT



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



class MarkovTrainService:
    messageDao = inject.attr(MessageDao)
    redis = inject.attr(Redis)


    async def train(self) -> None:
        await self.clear_cache()

        messages = await self.messageDao.select_longer_then(30)
        for message in messages:
            await self.markov_train_line(message['content'])


    async def clear_cache(self):
        await self.redis.flushall()


    async def markov_train_line(self, line: str) -> None:
        words = line.split()
        for i in range(len(words) - N):
            await self._increment_entry(
                ngram=tuple(words[i:i+N]), 
                next=words[i+N]
            )


    async def _increment_entry(self, ngram: NGram, next: str):
        key = "markov." + SEP.join(ngram)
        options: Dict[str, int] = await self.redis.hgetall(key) or {}
        options[next] = options.get(next, 0) + 1
        await self.redis.hset(key, mapping=options)



class MarkovService(MarkovTrainService):
    messageDao = inject.attr(MessageDao)
    redis = inject.attr(Redis)

    def __init__(self) -> None:
        super(MarkovTrainService).__init__()

    """
    async def generate_message(self) -> str:
        self._assert_can_generate_message()
        
        state = await self.simulate()
        message = escape_mentions(self.to_message(state))
        
        return message

    def _assert_can_generate_message(self) -> None:
        if self.state != MarkovState.READY:
            self._raise_not_ready()

        if not self.possible_starts:
            raise AssertionError("no possible starts")

    def _raise_not_ready(self) -> None:
        if self.state == MarkovState.TRAINING:
            raise AssertionError(f"markov is not ready, current state is {self.state}. Current progress {self.training_progress}%")
        raise AssertionError(f"markov is not ready, current state is {self.state}")

    @staticmethod
    def to_message(parts: List[str]) -> str:
        assert parts[0] == SOF, f"message parts must start with SOF, but was {parts}"
        assert parts[-1] == EOF, f"message parts must end with EOF, but was {parts}"
        return " ".join(parts[1:-1])
    
"""

class Markov(commands.Cog):
    service = MarkovService()

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot


    @commands.group(invoke_without_command=True)
    async def markov(self, ctx: Context, *_anything: str) -> None:
        try:
            # message = self.service.generate_message()
            await ctx.reply("no message")
        except Exception as ex:
            await ctx.send_error(str(ex))


    @markov.command(name='train', aliases=['retrain', 'grind'])
    @has_permissions(administrator=True)
    async def train(self, ctx: Context) -> None:
        await ctx.send("[Markov] Grinding ...")

        await self.service.train()
        
        await ctx.reply("[Markov] Finished grinding")

    """
    @commands.group(invoke_without_command=True)
    async def markov(self, ctx: Context, *_anything: str) -> None:
        try:
            message = self.service.generate_message()
            await ctx.reply(message)
        except Exception as ex:
            await ctx.send_error(str(ex))

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
        if len(self.possible_starts) == 0:
            log.info("no possible starts found, re-training")
            await self.train()
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
    """


async def setup(bot: "MasarykBOT") -> None:
    await bot.add_cog(Markov(bot))
