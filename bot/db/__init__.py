import inject

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