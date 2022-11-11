import asyncio
import logging
import os
from typing import Optional

import asyncpg
import inject

from .utils import Pool, Url


from .attachments import AttachmentDao
from .categories import CategoryDao
from .channels import ChannelDao
from .emojis import EmojiDao
from .guilds import GuildDao
from .message_emojis import MessageEmojiDao
from .messages import MessageDao
from .reactions import ReactionDao
from .roles import RoleDao
from .users import UserDao


log = logging.getLogger(__name__)


def connect_db(url: Url) -> Optional[Pool]:
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(asyncpg.create_pool(url, command_timeout=1280))

    except OSError:
        import re
        redacted_url = re.sub(r'\:(?!\/\/)[^\@]+', ":******", url)
        log.error("Failed to connect to database (%s)", redacted_url)
        return None

def inject_database(binder: inject.Binder) -> None:
    postgres_url = os.getenv("POSTGRES")
    if not postgres_url:
        return

    binder.bind(asyncpg.Pool, connect_db(postgres_url))
