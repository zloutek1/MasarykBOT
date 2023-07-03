from dependency_injector import containers, providers
from dependency_injector.providers import Singleton

from guild.repository import GuildRepository
from role.repository import RoleRepository


class Repository(containers.DeclarativeContainer):
    """
    Setup injections of the application's repositories
    """

    database = providers.Dependency()

    guild = Singleton(GuildRepository, session_factory=database.provided.session)
    role = Singleton(RoleRepository, session_factory=database.provided.session)
