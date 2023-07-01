from dependency_injector import containers, providers
from dependency_injector.providers import Singleton

from guild.repository import GuildRepository


class Repository(containers.DeclarativeContainer):
    database = providers.Dependency()

    guild = Singleton(GuildRepository, session_factory=database.provided.session)
