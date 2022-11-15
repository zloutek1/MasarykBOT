import inject

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


def setup_injections(binder: inject.Binder) -> None:
    binder.bind_to_constructor(AttachmentDao, AttachmentDao)
    binder.bind_to_constructor(CategoryDao, CategoryDao)
    binder.bind_to_constructor(ChannelDao, ChannelDao)
    binder.bind_to_constructor(EmojiDao, EmojiDao)
    binder.bind_to_constructor(GuildDao, GuildDao)
    binder.bind_to_constructor(MessageEmojiDao, MessageEmojiDao)
    binder.bind_to_constructor(MessageDao, MessageDao)
    binder.bind_to_constructor(ReactionDao, ReactionDao)
    binder.bind_to_constructor(RoleDao, RoleDao)
    binder.bind_to_constructor(UserDao, UserDao)