import inject

from .attachment import AttachmentBackup
from .bot import BotBackup
from .category import CategoryBackup
from .emoji import EmojiBackup
from .guild import GuildBackup
from .message import MessageBackup
from .message_emoji import MessageEmojiBackup
from .reaction import ReactionBackup
from .role import RoleBackup
from .text_channel import TextChannelBackup
from .user import UserBackup



def inject_backups(binder: inject.Binder):
    binder.bind(AttachmentBackup, AttachmentBackup)
    binder.bind(BotBackup, BotBackup)
    binder.bind(CategoryBackup, CategoryBackup)
    binder.bind(EmojiBackup, EmojiBackup)
    binder.bind(GuildBackup, GuildBackup)
    binder.bind(MessageBackup, MessageBackup)
    binder.bind(MessageEmojiBackup, MessageEmojiBackup)
    binder.bind(RoleBackup, RoleBackup)
    binder.bind(TextChannelBackup, TextChannelBackup)
    binder.bind(UserBackup, UserBackup)
