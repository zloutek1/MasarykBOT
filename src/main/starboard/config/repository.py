from typing import Type, Sequence

from sqlalchemy import select, or_

from core.domain.repository import DomainRepository
from starboard.config.model import StarboardConfig

__all__ = ["StarboardConfigRepository"]


class StarboardConfigRepository(DomainRepository[StarboardConfig]):
    @property
    def model(self) -> Type[StarboardConfig]:
        return StarboardConfig

    async def find_redirects(self, guild_id: int, starboard_channel_id: int) -> Sequence[StarboardConfig]:
        async with self.session_factory() as session:
            statement = select(self.model) \
                .where(self.model.guild_id == guild_id) \
                .where(self.model.starboard_channel_id == starboard_channel_id)
            result = await session.execute(statement)
            session.expunge_all()
            return result.scalars().all()

    async def find_starboards(self, guild_id: int, target_id: int) -> Sequence[StarboardConfig]:
        async with self.session_factory() as session:
            statement = select(self.model) \
                .where(self.model.guild_id == guild_id) \
                .where(or_(self.model.target_id == target_id, self.model.target_id.is_(None)))
            result = await session.execute(statement)
            session.expunge_all()
            return result.scalars().all()
