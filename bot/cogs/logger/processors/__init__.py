import discord
import inject
from discord.ext import commands

__all__ = [
    'Backup',
    'AttachmentBackup', 'BotBackup', 'CategoryBackup', 'EmojiBackup',
    'GuildBackup', 'MessageBackup', 'MessageEmojiBackup',
    'ReactionBackup', 'RoleBackup', 'ChannelBackup', 'ThreadBackup', 'UserBackup',
    'setup_injections'
]

from bot.cogs.logger.processors._base import Backup
from bot.cogs.logger.processors.attachment import AttachmentBackup
from bot.cogs.logger.processors.bot import BotBackup
from bot.cogs.logger.processors.category import CategoryBackup
from bot.cogs.logger.processors.channel import ChannelBackup
from bot.cogs.logger.processors.thread import ThreadBackup
from bot.cogs.logger.processors.emoji import EmojiBackup
from bot.cogs.logger.processors.guild import GuildBackup
from bot.cogs.logger.processors.message import MessageBackup
from bot.cogs.logger.processors.message_emoji import MessageEmojiBackup
from bot.cogs.logger.processors.reaction import ReactionBackup
from bot.cogs.logger.processors.role import RoleBackup
from bot.cogs.logger.processors.user import UserBackup
from bot.utils import MessageAttachment, MessageEmote, AnyEmote



def setup_injections(binder: inject.Binder) -> None:
    binder.bind_to_constructor(Backup[MessageAttachment], AttachmentBackup)
    binder.bind_to_constructor(Backup[commands.Bot], BotBackup)
    binder.bind_to_constructor(Backup[discord.CategoryChannel], CategoryBackup)
    binder.bind_to_constructor(Backup[AnyEmote], EmojiBackup)
    binder.bind_to_constructor(Backup[discord.Guild], GuildBackup)
    binder.bind_to_constructor(Backup[discord.Message], MessageBackup)
    binder.bind_to_constructor(Backup[MessageEmote], MessageEmojiBackup)
    binder.bind_to_constructor(Backup[discord.Reaction], ReactionBackup)
    binder.bind_to_constructor(Backup[discord.Role], RoleBackup)
    binder.bind_to_constructor(Backup[discord.abc.GuildChannel], ChannelBackup)
    binder.bind_to_constructor(Backup[discord.Thread], ThreadBackup)
    binder.bind_to_constructor(Backup[discord.User | discord.Member], UserBackup)
