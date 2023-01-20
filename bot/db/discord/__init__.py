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

from bot.db.discord.attachments import AttachmentRepository, AttachmentMapper, AttachmentEntity
from bot.db.discord.categories import CategoryRepository, CategoryMapper, CategoryEntity
from bot.db.discord.channels import ChannelRepository, ChannelMapper, ChannelEntity
from bot.db.discord.threads import ThreadRepository, ThreadMapper, ThreadEntity
from bot.db.discord.emojis import EmojiRepository, EmojiMapper, EmojiEntity
from bot.db.discord.guilds import GuildRepository, GuildMapper, GuildEntity
from bot.db.discord.message_emojis import MessageEmojiRepository, MessageEmojiMapper, MessageEmojiEntity
from bot.db.discord.messages import MessageRepository, MessageMapper, MessageEntity
from bot.db.discord.reactions import ReactionRepository, ReactionMapper, ReactionEntity
from bot.db.discord.roles import RoleRepository, RoleMapper, RoleEntity
from bot.db.discord.users import UserRepository, UserMapper, UserEntity

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
