from dependency_injector import containers, providers

from core.database import Database
from core.inject.repository import Repository


class Inject(containers.DeclarativeContainer):
    config = providers.Configuration(ini_files=["resources/application.ini"])

    database = providers.Singleton(Database, url=config.database.url)

    repository = providers.Container(Repository, database=database)
