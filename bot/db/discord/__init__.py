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
    binder.bind(AttachmentDao, AttachmentDao())
    binder.bind(CategoryDao, CategoryDao())
    binder.bind(ChannelDao, ChannelDao())
    binder.bind(EmojiDao, EmojiDao())
    binder.bind(GuildDao, GuildDao())
    binder.bind(MessageEmojiDao, MessageEmojiDao())
    binder.bind(MessageDao, MessageDao())
    binder.bind(ReactionDao, ReactionDao())
    binder.bind(RoleDao, RoleDao())
    binder.bind(UserDao, UserDao())