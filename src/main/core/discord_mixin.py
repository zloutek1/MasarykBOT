from tokenize import String

from sqlalchemy import Column


class DiscordMixin:
    discord_id = Column(String, nullable=False)
