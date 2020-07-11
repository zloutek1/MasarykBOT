import logging
import sys


def setup_logging():
    """
    sets up custom logging into self.log variable

    set format to
    [2019-09-29 18:51:04] [INFO   ] core.logger: Begining backup
    """

    logging.getLogger('discord').setLevel(logging.INFO)
    logging.getLogger('discord.http').setLevel(logging.WARNING)

    log = logging.getLogger()
    log.setLevel(logging.INFO)

    dt_fmt = '%Y-%m-%d %H:%M:%S'
    fmt = logging.Formatter('[{asctime}] [{levelname:<7}] {name}: {message}', dt_fmt, style='{')

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(fmt)
    log.addHandler(handler)
