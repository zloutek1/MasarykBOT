from dependency_injector import containers
from dependency_injector.providers import List

from sync import setup as setup_sync


class Cog(containers.DeclarativeContainer):
    sync = setup_sync

    all = List(
        sync
    )
