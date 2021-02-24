import logging
import sys
from pathlib import Path

from rich.logging import RichHandler


def setup_logging():
    """
    sets up custom logging into self.log variable

    set format to
    [2019-09-29 18:51:04] [INFO   ] core.logger: Begining backup
    """

    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.http').setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.INFO)

    log = logging.getLogger()

    shell_handler = RichHandler()
    file_handler = logging.FileHandler(Path("logs", "bot.log"))

    log.setLevel(logging.DEBUG)
    shell_handler.setLevel(logging.INFO)
    file_handler.setLevel(logging.DEBUG)

    fmt_date = '%Y-%m-%d %H:%M:%S'
    fmt_shell = '{message}'
    fmt_file = '{asctime} | {levelname:<7} | {filename}:{lineno} | {message}'

    shell_handler.setFormatter(logging.Formatter(fmt_shell, fmt_date, style='{'))
    file_handler.setFormatter(logging.Formatter(fmt_file, fmt_date, style='{'))

    log.addHandler(shell_handler)
    log.addHandler(file_handler)
