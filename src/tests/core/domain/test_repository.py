from dataclasses import dataclass

from assertpy import assert_that
from sqlalchemy import Column, String
from sqlalchemy.orm import Mapped

import helpers
from core.database import Entity
from core.domain.mixin import DomainMixin
from core.domain.repository import DomainRepository


@dataclass
class DomainItem(Entity, DomainMixin):
    __tablename__ = "test_domain_item"
    name: Mapped[str] = Column(String)


class DomainItemRepository(DomainRepository[DomainItem]):
    @property
    def model(self): return DomainItem


class Test(helpers.TestBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.repository = DomainItemRepository(session_factory=cls.database.session)

    async def test_find_all(self):
        # Create test records
        item1 = DomainItem()
        item1.name = 'Alice'

        item2 = DomainItem()
        item2.name = 'Bob'

        async with self.session.begin():
            self.session.add_all([item1, item2])
            await self.session.commit()
            self.session.expunge_all()

        # Call the method being tested
        result = await self.repository.find_all()

        # Assert the expected results
        assert_that(result).contains_only(item1, item2)

    async def test_find(self):
        # Create a test record
        item = DomainItem()
        item.name = 'John'

        async with self.session.begin():
            self.session.add(item)
            await self.session.commit()
            self.session.expunge_all()

        # Call the method being tested
        result = await self.repository.find(item.id)

        # Assert the expected result
        assert_that(result).is_equal_to(item)

    async def test_create(self):
        # Call the method being tested
        item = DomainItem()
        item.name = 'Josh'
        result = await self.repository.create(item)

        # Assert the expected result
        assert_that(result).is_instance_of(DomainItem)
        assert_that(result.name).is_equal_to('Josh')

    async def test_update(self):
        # Create a test record
        item = DomainItem()
        item.name = 'Amelia'

        async with self.session.begin():
            self.session.add(item)
            await self.session.commit()
            self.session.expunge_all()

        # Call the method being tested
        item.name = 'Alicia'
        updated_item = await self.repository.update(item)

        # Assert the expected result
        assert_that(updated_item.name).is_equal_to('Alicia')
        assert_that(item).is_equal_to(await self.repository.find(item.id))

    async def test_delete(self):
        # Create a test record
        item = DomainItem()
        item.name = 'Guy'

        async with self.session.begin():
            self.session.add(item)
            await self.session.commit()
            self.session.expunge_all()

        # Call the method being tested
        await self.repository.delete(item.id)

        # Assert the record has been deleted
        result = await self.repository.find(item.id)
        assert_that(result).is_none()
