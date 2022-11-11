import inject

from .discord import (AttachmentDao, CategoryDao, ChannelDao, EmojiDao,
                      GuildDao, MessageDao, MessageEmojiDao, ReactionDao,
                      RoleDao, UserDao)
from .discord import setup_injections as setup_discord_injections


def setup_injections(binder: inject.Binder) -> None:
    binder.install(setup_discord_injections)