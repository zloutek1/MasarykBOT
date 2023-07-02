from dependency_injector import containers
from dependency_injector.providers import List

from error import setup as setup_error
from sync import setup as setup_sync


class Cog(containers.DeclarativeContainer):
    sync = setup_sync
    error = setup_error

    all = List(
        sync,
        error
    )
