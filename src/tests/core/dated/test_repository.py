import unittest
from dataclasses import dataclass

from assertpy import assert_that
from sqlalchemy import Column, String, select
from sqlalchemy.orm import Mapped

from core.database import Entity, Database
from core.dated.mixin import DatedMixin
from core.dated.repository import DatedRepository


@dataclass
class TestDatedItem(Entity, DatedMixin):
    __tablename__ = "test_dated_item"
    name: Mapped[str] = Column(String)


class TestDatedItemRepository(DatedRepository[TestDatedItem]):
    @property
    def model(self): return TestDatedItem


class Test(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        database = Database('sqlite+aiosqlite:///:memory:')
        cls.database = database
        cls.repository = TestDatedItemRepository(session_factory=database.session)

    async def asyncSetUp(self) -> None:
        await self.database.create_database()
        self.session = await self.database.session().__aenter__()

    async def asyncTearDown(self) -> None:
        async with self.database._engine.begin() as conn:
            await conn.run_sync(Entity.metadata.drop_all)

    async def test_find_all(self):
        # Create test records
        item1 = TestDatedItem()
        item1.name = 'Alice'

        item2 = TestDatedItem()
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
        item = TestDatedItem()
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
        item = TestDatedItem()
        item.name = 'Josh'
        result = await self.repository.create(item)

        # Assert the expected result
        assert_that(result).is_instance_of(TestDatedItem)
        assert_that(result.name).is_equal_to('Josh')

    async def test_update(self):
        # Create a test record
        item = TestDatedItem()
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
        item = TestDatedItem()
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

        async with self.session.begin():
            statement = select(TestDatedItem).where(TestDatedItem.id == item.id)
            result = await self.session.execute(statement)
            result = result.scalars().first()
            self.session.expunge_all()

        assert_that(result).is_not_none()
        assert_that(result.deleted).is_not_none()

    async def test_hard_delete(self):
        # Create a test record
        item = TestDatedItem()
        item.name = 'Guy'

        async with self.session.begin():
            self.session.add(item)
            await self.session.commit()
            self.session.expunge_all()

        # Call the method being tested
        await self.repository.hard_delete(item.id)

        # Assert the record has been deleted
        result = await self.repository.find(item.id)
        assert_that(result).is_none()

        async with self.session.begin():
            statement = select(TestDatedItem).where(TestDatedItem.id == item.id)
            result = await self.session.execute(statement)
            result = result.scalars().first()
            self.session.expunge_all()

        assert_that(result).is_none()
