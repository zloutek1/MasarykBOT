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

from __oild.bot.cogs.logger.processors._base import Backup
from __oild.bot.cogs.logger.processors.attachment import AttachmentBackup
from __oild.bot.cogs.logger.processors.bot import BotBackup
from src.bot import CategoryBackup
from __oild.bot.cogs.logger.processors.channel import ChannelBackup
from __oild.bot.cogs.logger.processors.thread import ThreadBackup
from __oild.bot.cogs.logger.processors.emoji import EmojiBackup
from __oild.bot.cogs.logger.processors.guild import GuildBackup
from src.bot import MessageBackup
from __oild.bot.cogs.logger.processors.message_emoji import MessageEmojiBackup
from __oild.bot.cogs.logger.processors.reaction import ReactionBackup
from src.bot import RoleBackup
from __oild.bot.cogs.logger.processors.user import UserBackup
from src.bot import MessageAttachment, MessageEmote, AnyEmote


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
