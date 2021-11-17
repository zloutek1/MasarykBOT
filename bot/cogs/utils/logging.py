import logging
import os
from logging import FileHandler, Formatter
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from rich.logging import RichHandler

def my_namer(default_name):
    # This will be called when doing the log rotation
    # default_name is the default filename that would be assigned, e.g. Rotate_Test.txt.YYYY-MM-DD
    # Do any manipulations to that name here, for example this changes the name to Rotate_Test.YYYY-MM-DD.txt
    base_filename, ext, date = default_name.split(".")
    return f"{base_filename}.{date}.{ext}"

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

    filename = Path("logs", "bot.log")
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    all_file_handler = TimedRotatingFileHandler(filename, when='midnight')
    all_file_handler.namer = my_namer

    filename = Path("logs", "warn.log")
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    warn_file_handler = FileHandler(filename, mode='a')

    log.setLevel(logging.DEBUG)
    shell_handler.setLevel(logging.INFO)
    all_file_handler.setLevel(logging.DEBUG)
    warn_file_handler.setLevel(logging.WARNING)

    fmt_date = '%Y-%m-%d %H:%M:%S'
    fmt_shell = '{message}'
    fmt_file = '{asctime} | {levelname:<7} | {filename:>20}:{lineno:<4} | {message}'

    shell_handler.setFormatter(Formatter(fmt_shell, fmt_date, style='{'))
    all_file_handler.setFormatter(Formatter(fmt_file, fmt_date, style='{'))
    warn_file_handler.setFormatter(Formatter(fmt_file, fmt_date, style='{'))

    log.addHandler(shell_handler)
    log.addHandler(all_file_handler)
    log.addHandler(warn_file_handler)
