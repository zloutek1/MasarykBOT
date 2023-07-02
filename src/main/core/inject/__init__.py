from dependency_injector import containers, providers

from core.database import Database
from core.inject.cog import Cog
from core.inject.repository import Repository


class Inject(containers.DeclarativeContainer):
    config = providers.Configuration(yaml_files=["resources/application.yaml"])

    database = providers.Singleton(Database, url=config.database.url)

    repository = providers.Container(Repository, database=database)

    cog = providers.Container(Cog)
