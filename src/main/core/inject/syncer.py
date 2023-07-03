from dependency_injector import containers, providers

from role.syncer import RoleSyncer


class Syncer(containers.DeclarativeContainer):
    """
    Setup injections of the application's synchronizes
    """

    role_repository = providers.Dependency()

    role = providers.Singleton(RoleSyncer, repository=role_repository)

    all = providers.List(
        role
    )
