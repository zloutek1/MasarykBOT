import inject

__all__ = [
    "AttachmentRepository", "AttachmentMapper", "AttachmentEntity",
    "CategoryRepository", "CategoryMapper", "CategoryEntity",
    "ChannelRepository", "ChannelMapper", "ChannelEntity",
    "ThreadRepository", "ThreadMapper", "ThreadEntity",
    "EmojiRepository", "EmojiMapper", "EmojiEntity",
    "GuildRepository", "GuildMapper", "GuildEntity",
    "MessageEmojiRepository", "MessageEmojiMapper", "MessageEmojiEntity",
    "MessageRepository", "MessageMapper", "MessageEntity",
    "ReactionRepository", "ReactionMapper", "ReactionEntity",
    "RoleRepository", "RoleMapper", "RoleEntity",
    "UserRepository", "UserMapper", "UserEntity",
    "setup_injections"
]

from __oild.bot.db.discord.attachments import AttachmentRepository, AttachmentMapper, AttachmentEntity
from __oild.bot.db.discord.categories import CategoryRepository, CategoryMapper, CategoryEntity
from __oild.bot.db.discord.channels import ChannelRepository, ChannelMapper, ChannelEntity
from __oild.bot.db.discord.threads import ThreadRepository, ThreadMapper, ThreadEntity
from src.bot import EmojiRepository, EmojiMapper, EmojiEntity
from src.bot import GuildRepository, GuildMapper, GuildEntity
from src.bot import MessageEmojiRepository, MessageEmojiMapper, MessageEmojiEntity
from src.bot import MessageRepository, MessageMapper, MessageEntity
from __oild.bot.db.discord.reactions import ReactionRepository, ReactionMapper, ReactionEntity
from src.bot import RoleRepository, RoleMapper, RoleEntity
from __oild.bot.db.discord.users import UserRepository, UserMapper, UserEntity

REPOSITORIES = (GuildRepository, RoleRepository, UserRepository, EmojiRepository, CategoryRepository, ChannelRepository,
                ThreadRepository, MessageRepository, AttachmentRepository, ReactionRepository, MessageEmojiRepository)
MAPPERS = (GuildMapper, RoleMapper, UserMapper, EmojiMapper, CategoryMapper, ChannelMapper, MessageMapper,
           ThreadMapper, AttachmentMapper, ReactionMapper, MessageEmojiMapper)
ENTITIES = (GuildEntity, RoleEntity, UserEntity, EmojiEntity, CategoryEntity, ChannelEntity,
            ThreadEntity, MessageEntity, AttachmentEntity, ReactionEntity, MessageEmojiEntity)



def setup_injections(binder: inject.Binder) -> None:
    for repo_type in REPOSITORIES:
        binder.bind_to_constructor(repo_type, repo_type)

    for mapper_type in MAPPERS:
        binder.bind_to_constructor(mapper_type, mapper_type)
