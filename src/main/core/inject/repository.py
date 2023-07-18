from dependency_injector import containers, providers
from dependency_injector.providers import Singleton

from channel.category.repository import CategoryChannelRepository
from channel.text.repository import TextChannelRepository
from guild.repository import GuildRepository
from message.repository import MessageRepository
from role.repository import RoleRepository
from starboard.config.repository import StarboardConfigRepository


class Repository(containers.DeclarativeContainer):
    """
    Setup injections of the application's repositories
    """

    database = providers.Dependency()

    guild = Singleton(GuildRepository, session_factory=database.provided.session)
    role = Singleton(RoleRepository, session_factory=database.provided.session)
    category_channel = Singleton(CategoryChannelRepository, session_factory=database.provided.session)
    text_channel = Singleton(TextChannelRepository, session_factory=database.provided.session)
    message = Singleton(MessageRepository, session_factory=database.provided.session)

    starboard_config = Singleton(StarboardConfigRepository, session_factory=database.provided.session)
