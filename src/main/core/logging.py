import logging
import sys


def setup_logging() -> None:
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.http').setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.INFO)

    log = logging.getLogger()
    shell_handler = logging.StreamHandler(sys.stdout)  # RichHandler()

    log.setLevel(logging.DEBUG)
    shell_handler.setLevel(logging.INFO)

    log.addHandler(shell_handler)
