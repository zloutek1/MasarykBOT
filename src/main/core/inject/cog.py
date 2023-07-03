from dependency_injector import containers, providers

from error import setup as setup_error
from sync import setup as setup_sync


class Cog(containers.DeclarativeContainer):
    """
    Setup injections of the application cog's
    """

    sync = setup_sync
    error = setup_error

    all = providers.List(
        sync,
        error
    )
