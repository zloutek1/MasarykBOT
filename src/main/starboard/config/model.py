from sqlalchemy import Column, BigInteger, Index, Integer
from sqlalchemy.orm import Mapped

from core.database import Entity
from core.domain.mixin import DomainMixin

__all__ = ["StarboardConfig"]


class StarboardConfig(Entity, DomainMixin):
    __tablename__ = "starboard_config"

    guild_id: Mapped[int] = Column(BigInteger, nullable=False)
    starboard_channel_id: Mapped[int] = Column(BigInteger, nullable=False)
    target_id: Mapped[int | None] = Column(BigInteger, nullable=True)
    min_limit: Mapped[int] = Column(Integer, nullable=False, default=10)

    idx_guild_target_starboard = Index(
        'idx_guild_target_starboard_channel_unique',
        guild_id, target_id, starboard_channel_id,
        unique=True)

    def __repr__(self) -> str:
        attrs = (
            ('id', self.id),
            ('guild_id', self.guild_id),
            ('target_id', self.target_id),
            ('starboard_channel_id', self.starboard_channel_id),
        )
        inner = ' '.join('%s=%r' % t for t in attrs)
        return f'<{type(self).__name__} {inner}>'
