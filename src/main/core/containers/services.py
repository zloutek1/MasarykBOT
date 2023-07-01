import sqlalchemy
from dependency_injector import containers, providers


class Gateways(containers.DeclarativeContainer):
    config = providers.Configuration()

    database_client = providers.Singleton(
        sqlalchemy.create_engine,
        config.database.url,
    )


class Services(containers.DeclarativeContainer):
    config = providers.Configuration()


class App(containers.DeclarativeContainer):
    config = providers.Configuration(yaml_files=["core.yml"])

    gateways = providers.Container(
        Gateways,
        config=config.gateway
    )

    services = providers.Container(
        Services,
        config=config.service
    )
