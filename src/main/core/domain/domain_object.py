import uuid

from sqlalchemy import Column, UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class DomainObject(Base):
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
