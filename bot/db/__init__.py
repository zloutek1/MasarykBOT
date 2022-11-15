import asyncio
import asyncpg
import inject

from bot.db.utils import Pool, Url

from .discord import (AttachmentDao, CategoryDao, ChannelDao, EmojiDao,
                      GuildDao, MessageDao, MessageEmojiDao, ReactionDao,
                      RoleDao, UserDao)
from .discord import setup_injections as setup_discord_injections
#from .activity import ActivityDao
#from .emojiboard import EmojiboardDao
from .leaderboard import LeaderboardDao
#from .seasons import SeasonDao
#from .subjects import SubjectDao
#from .tags import TagDao



def setup_injections(binder: inject.Binder) -> None:
    binder.install(setup_discord_injections)



async def connect_db(url: Url) -> Pool:
    pool = None
    attempts = 0
    while pool is None:
        pool = await asyncpg.create_pool(url, command_timeout=1280)
        await asyncio.sleep(1)
        
        attempts += 1
        if attempts > 1_000:
            raise TimeoutError("tried to connect over 1000 times")
    return pool