from dependency_injector import containers, providers

from error import setup as setup_error
from starboard import setup as setup_starboard
from sync import setup as setup_sync


class Cog(containers.DeclarativeContainer):
    """
    Setup injections of the application cog's
    """

    sync = setup_sync
    error = setup_error
    starboard = setup_starboard

    all = providers.List(
        sync,
        error,
        starboard
    )
