import asyncio
import logging
import socket
from typing import Optional

import asyncpg
import inject

from bot.db.utils import Pool, Record, Url

from .discord import (AttachmentMapper, CategoryMapper, ChannelMapper, EmojiMapper,
                      GuildMapper, MessageMapper, ReactionMapper,
                      RoleMapper, UserMapper)
from .discord import (AttachmentRepository, CategoryRepository, ChannelRepository, EmojiRepository,
                      GuildRepository, MessageRepository, ReactionRepository,
                      RoleRepository, UserRepository)
from .discord import setup_injections as setup_discord_injections

from .muni import (FacultyRepository, CourseRepository)
from .muni import setup_injections as setup_muni_injections

from .leaderboard import LeaderboardRepository
from .logger import LoggerRepository

log = logging.getLogger(__name__)


def setup_injections(binder: inject.Binder) -> None:
    binder.install(setup_discord_injections)
    binder.install(setup_muni_injections)


async def connect_db(url: Url) -> Optional[Pool]:
    try:
        pool = None
        attempts = 0
        while pool is None:
            pool = await asyncpg.create_pool(url, command_timeout=1280)
            await asyncio.sleep(1)

            attempts += 1
            if attempts > 1_000:
                raise TimeoutError("tried to connect over 1000 times")
        return pool
    except (socket.gaierror, OSError) as ex:
        log.error("Failed to connect to database: %s", ex)
        return None
