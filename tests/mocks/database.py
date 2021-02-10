import collections
import unittest.mock
from typing import Optional, List, Union, get_origin, get_args
import datetime

from bot.cogs.utils import db
from asyncpg.protocol.protocol import _create_record as Record

def record(func):
    """
    return a Record with column names from annotated variables
    """

    fields = func.__annotations__.keys()
    mapping = collections.OrderedDict((val, idx) for (idx, val) in enumerate(fields))

    def pos(n):
        return {
            1: '1st',
            2: '2nd',
            3: '3rd',
        }.get(n, f'{n}th')

    def type_check(kwargs):
        for i, (field, ftype) in enumerate(func.__annotations__.items()):
            if get_origin(ftype) is None and not isinstance(kwargs[field], ftype):
                raise TypeError(f"Couldn't match expected type {ftype} with actual type {type(kwargs[field])} in {pos(i+1)} argument {field}")

            elif get_origin(ftype) is not None:
                if not type_check_generic(kwargs[field], ftype):
                    raise TypeError(f"Couldn't match expected type {ftype} with actual type {type(kwargs[field])} in {pos(i+1)} argument {field}")


    def type_check_generic(value, ftype):
        if get_origin(ftype) is Union:
            return any(type_check_generic(value, vtype) for vtype in get_args(ftype))

        if get_origin(ftype) is list:
            vtype = get_args(ftype)[0]
            return isinstance(value, list) and all(type_check_generic(inner, vtype) for inner in value)

        return isinstance(value, ftype)

    def wrapper(**kwargs):
        """
        require all key-word arguments to be filled and have required type
        """
        kwargs = func.__kwdefaults__ | kwargs

        missing = [field for field in func.__annotations__ if field not in kwargs]
        if missing:
            raise TypeError(f"{func.__qualname__} missing {len(missing)} required keyword-only arguments: {', '.join(missing)}")

        type_check(kwargs)

        elems = tuple(kwargs[key] for key in mapping)
        return Record(mapping, elems)
    return wrapper

@record
def MockLeaderboardRecord(*, row_number: int, author_id: int, author: str, sent_total: int):
    pass

@record
def MockSubjectRecord(*, faculty: str, code: str, name: str, url: str, terms: List[str],
                         created_at: datetime.datetime, edited_at: Optional[datetime.datetime] = None, deleted_at: Optional[datetime.datetime] = None):
    pass

class MockPool(unittest.mock.MagicMock):
    pass

def MockDatabase():
    database = db.Database(MockPool())

    tables = [table for table in vars(database).values() if isinstance(table, db.Table)]
    for table in tables:
        for attr in dir(table):
            if attr.startswith('_'):
                continue

            if attr in ['prepare', 'prepare_one']:
                continue

            setattr(table, attr, unittest.mock.AsyncMock())

    return database