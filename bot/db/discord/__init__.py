from typing import List
import inject

from .attachments import AttachmentRepository, AttachmentMapper
from .categories import CategoryRepository, CategoryMapper
from .channels import ChannelRepository, ChannelMapper
from .emojis import EmojiRepository, EmojiMapper
from .guilds import GuildRepository, GuildMapper
from .message_emojis import MessageEmojiRepository
from .messages import MessageRepository, MessageMapper
from .reactions import ReactionRepository, ReactionMapper
from .roles import RoleRepository, RoleMapper
from .users import UserRepository, UserMapper

REPOSITORIES = (GuildRepository, RoleRepository, UserRepository, EmojiRepository, CategoryRepository, ChannelRepository,
                MessageRepository, MessageEmojiRepository, AttachmentRepository, ReactionRepository)
MAPPERS = (GuildMapper, RoleMapper, UserMapper, EmojiMapper, CategoryMapper, ChannelMapper, MessageMapper,
           AttachmentMapper, ReactionMapper)


def setup_injections(binder: inject.Binder) -> None:
    for repo_type in REPOSITORIES:
        binder.bind_to_constructor(repo_type, repo_type)

    for mapper_type in MAPPERS:
        binder.bind_to_constructor(mapper_type, mapper_type)
