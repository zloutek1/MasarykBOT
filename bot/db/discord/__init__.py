import inject

__all__ = [
    "AttachmentRepository", "AttachmentMapper", "AttachmentEntity",
    "CategoryRepository", "CategoryMapper", "CategoryEntity",
    "ChannelRepository", "ChannelMapper", "ChannelEntity",
    "EmojiRepository", "EmojiMapper", "EmojiEntity",
    "GuildRepository", "GuildMapper", "GuildEntity",
    "MessageEmojiRepository", "MessageEmojiMapper", "MessageEmojiEntity",
    "MessageRepository", "MessageMapper", "MessageEntity",
    "ReactionRepository", "ReactionMapper", "ReactionEntity",
    "RoleRepository", "RoleMapper", "RoleEntity",
    "UserRepository", "UserMapper", "UserEntity",
    "setup_injections"
]

from .attachments import AttachmentRepository, AttachmentMapper, AttachmentEntity
from .categories import CategoryRepository, CategoryMapper, CategoryEntity
from .channels import ChannelRepository, ChannelMapper, ChannelEntity
from .emojis import EmojiRepository, EmojiMapper, EmojiEntity
from .guilds import GuildRepository, GuildMapper, GuildEntity
from .message_emojis import MessageEmojiRepository, MessageEmojiMapper, MessageEmojiEntity
from .messages import MessageRepository, MessageMapper, MessageEntity
from .reactions import ReactionRepository, ReactionMapper, ReactionEntity
from .roles import RoleRepository, RoleMapper, RoleEntity
from .users import UserRepository, UserMapper, UserEntity

REPOSITORIES = (GuildRepository, RoleRepository, UserRepository, EmojiRepository, CategoryRepository, ChannelRepository,
                MessageRepository, AttachmentRepository, ReactionRepository, MessageEmojiRepository)
MAPPERS = (GuildMapper, RoleMapper, UserMapper, EmojiMapper, CategoryMapper, ChannelMapper, MessageMapper,
           AttachmentMapper, ReactionMapper, MessageEmojiMapper)
ENTITIES = (GuildEntity, RoleEntity, UserEntity, EmojiEntity, CategoryEntity, ChannelEntity,
            MessageEntity, AttachmentEntity, ReactionEntity, MessageEmojiEntity)



def setup_injections(binder: inject.Binder) -> None:
    for repo_type in REPOSITORIES:
        binder.bind_to_constructor(repo_type, repo_type)

    for mapper_type in MAPPERS:
        binder.bind_to_constructor(mapper_type, mapper_type)
