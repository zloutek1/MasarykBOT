import logging

from rich.logging import RichHandler


def setup_logging() -> None:
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.http').setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.INFO)

    log = logging.getLogger()
    shell_handler = RichHandler()

    log.setLevel(logging.DEBUG)
    shell_handler.setLevel(logging.INFO)

    log.addHandler(shell_handler)
