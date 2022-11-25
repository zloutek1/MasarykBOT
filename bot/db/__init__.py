import asyncio
import asyncpg
import inject

from bot.db.utils import Pool, Record, Url

from .discord import (AttachmentRepository, CategoryRepository, ChannelRepository, EmojiRepository,
                      GuildRepository, MessageRepository, ReactionRepository, 
                      RoleRepository, UserRepository)
from .discord import (AttachmentMapper, CategoryMapper, ChannelMapper, EmojiMapper,
                      GuildMapper, MessageMapper, ReactionMapper,
                      RoleMapper, UserMapper)
from .discord import setup_injections as setup_discord_injections
#from .activity import ActivityDao
#from .emojiboard import EmojiboardDao
from .logger import LoggerRepository
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