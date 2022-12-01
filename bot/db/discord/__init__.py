from typing import List
import inject

from .attachments import AttachmentRepository, AttachmentMapper, AttachmentEntity
from .categories import CategoryRepository, CategoryMapper, CategoryEntity
from .channels import ChannelRepository, ChannelMapper, ChannelEntity
from .emojis import EmojiRepository, EmojiMapper, EmojiEntity
from .guilds import GuildRepository, GuildMapper, GuildEntity
from .messages import MessageRepository, MessageMapper, MessageEntity
from .reactions import ReactionRepository, ReactionMapper, ReactionEntity
from .roles import RoleRepository, RoleMapper, RoleEntity
from .users import UserRepository, UserMapper, UserEntity

REPOSITORIES = (GuildRepository, RoleRepository, UserRepository, EmojiRepository, CategoryRepository, ChannelRepository,
                MessageRepository, AttachmentRepository, ReactionRepository)
MAPPERS = (GuildMapper, RoleMapper, UserMapper, EmojiMapper, CategoryMapper, ChannelMapper, MessageMapper,
           AttachmentMapper, ReactionMapper)
ENTITIES = (GuildEntity, RoleEntity, UserEntity, EmojiEntity, CategoryEntity, ChannelEntity,
            MessageEntity, AttachmentEntity, ReactionEntity)



def setup_injections(binder: inject.Binder) -> None:
    for repo_type in REPOSITORIES:
        binder.bind_to_constructor(repo_type, repo_type)

    for mapper_type in MAPPERS:
        binder.bind_to_constructor(mapper_type, mapper_type)
