import inject

from .discord import *
from .discord import setup_injections as setup_discord_injections



def setup_injections(binder: inject.Binder) -> None:
    setup_discord_injections(binder)