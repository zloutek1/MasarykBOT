from dependency_injector import containers, providers
from dependency_injector.wiring import register_loader_containers

from core.database import Database
from core.inject.cog import Cog
from core.inject.repository import Repository
from core.inject.syncer import Syncer


class Inject(containers.DeclarativeContainer):
    config = providers.Configuration(yaml_files=["resources/application.yaml"])

    database: Database = providers.Singleton(
        Database,
        url=config.database.url,
        echo=config.database.echo
    )

    repository: Repository = providers.Container(Repository, database=database)

    cog: Cog = providers.Container(Cog)

    syncer: Syncer = providers.Container(Syncer, role_repository=repository.role)


def setup_injections():
    container = Inject()
    container.wire(modules=['__main__'])
    register_loader_containers(container)
