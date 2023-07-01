from core.dated.repository import DatedRepository
from guild.model import Guild


class GuildRepository(DatedRepository[Guild]):
    @property
    def model(self):
        return Guild
