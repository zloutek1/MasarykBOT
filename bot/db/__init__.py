import asyncio
import logging
import socket
from typing import Optional

import asyncpg
import inject

__all__ = [
    "UnitOfWork", "Url", "Page", "Pool", "Record", "DBConnection",

    "AttachmentMapper", "CategoryMapper", "ChannelMapper", "ThreadMapper", "EmojiMapper",
    "GuildMapper", "MessageMapper", "MessageEmojiMapper", "ReactionMapper",
    "RoleMapper", "UserMapper",

    "AttachmentRepository", "CategoryRepository", "ChannelRepository", "ThreadRepository", "EmojiRepository",
    "GuildRepository", "MessageRepository", "MessageEmojiRepository", "ReactionRepository",
    "RoleRepository", "UserRepository",

    "AttachmentEntity", "CategoryEntity", "ChannelEntity", "ThreadEntity", "EmojiEntity",
    "GuildEntity", "MessageEntity", "MessageEmojiEntity", "ReactionEntity",
    "RoleEntity", "UserEntity",

    "CourseRepository", "StudentRepository", "CourseEntity", "StudentEntity", "FacultyRepository", "FacultyEntity",

    "LeaderboardRepository", "LoggerRepository", "LeaderboardEntity", "LoggerEntity", "MarkovRepository", "MarkovEntity",
    "setup_injections",
    "connect_db"
]

# ---- utils ----
from bot.db.utils import UnitOfWork, Url, Page, Pool, Record, DBConnection

# ---- discord ----
from bot.db.discord import (AttachmentMapper, CategoryMapper, ChannelMapper, EmojiMapper,
                            GuildMapper, MessageMapper, MessageEmojiMapper, ReactionMapper,
                            ThreadMapper, RoleMapper, UserMapper)
from bot.db.discord import (AttachmentRepository, CategoryRepository, ChannelRepository, EmojiRepository,
                            GuildRepository, MessageRepository, MessageEmojiRepository, ReactionRepository,
                            ThreadRepository, RoleRepository, UserRepository)
from bot.db.discord import (AttachmentEntity, CategoryEntity, ChannelEntity, EmojiEntity,
                            GuildEntity, MessageEntity, MessageEmojiEntity, ReactionEntity,
                            ThreadEntity, RoleEntity, UserEntity)
from bot.db.discord import setup_injections as setup_discord_injections

# ---- muni ----
from bot.db.muni import (CourseRepository, StudentRepository, FacultyRepository)
from bot.db.muni import (CourseEntity, StudentEntity, FacultyEntity)
from bot.db.muni import setup_injections as setup_muni_injections

# ---- cogs ----
from bot.db.cogs import (LeaderboardRepository, LoggerRepository, MarkovRepository)
from bot.db.cogs import (LeaderboardEntity, LoggerEntity, MarkovEntity)
from bot.db.cogs import setup_injections as setup_cogs_injections

log = logging.getLogger(__name__)


def setup_injections(binder: inject.Binder) -> None:
    binder.install(setup_discord_injections)
    binder.install(setup_muni_injections)
    binder.install(setup_cogs_injections)

    binder.bind_to_constructor(UnitOfWork, UnitOfWork)


async def connect_db(url: Url) -> Optional[Pool]:
    pool: Pool | None = None
    attempts = 0
    while pool is None:
        try:
            pool = await asyncpg.create_pool(url, command_timeout=1280)
        except (socket.gaierror, OSError) as ex:
            log.error("Failed to connect to database: %s", ex)
            return None

        await asyncio.sleep(1)

        attempts += 1
        if attempts > 1_000:
            raise TimeoutError("tried to connect over 1000 times")
    return pool
