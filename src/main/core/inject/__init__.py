from dependency_injector import containers, providers
from dependency_injector.wiring import register_loader_containers

from core.database import Database
from core.inject.cog import Cog
from core.inject.repository import Repository


class Inject(containers.DeclarativeContainer):
    config = providers.Configuration(yaml_files=["resources/application.yaml"])

    database = providers.Singleton(
        Database,
        url=config.database.url,
        echo=config.database.echo
    )

    repository = providers.Container(Repository, database=database)

    cog = providers.Container(Cog)


def setup_injections():
    container = Inject()
    container.wire(modules=['__main__'])
    register_loader_containers(container)
