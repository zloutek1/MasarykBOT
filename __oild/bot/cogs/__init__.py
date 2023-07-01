import inject

from __oild.bot.cogs.logger import setup_injections as setup_logger_injections


def setup_injections(binder: inject.Binder) -> None:
    binder.install(setup_logger_injections)
