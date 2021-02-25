import sys
import collections
import datetime
from functools import wraps
from dataclasses import dataclass

import unittest.mock


from typing import Optional, List, Union, get_origin, get_args


#from bot.cogs.utils import db
from asyncpg.protocol.protocol import _create_record as Record

"""

def MockDatabase():
    database = db.Database(MockPool())

    tables = [table for table in vars(database).values() if isinstance(table, db.Table)]
    for table in tables:
        for attr in dir(table):
            if attr.startswith('_'):
                continue

            if attr in ['prepare', 'prepare_one', 'prepare_from_message']:
                continue

            setattr(table, attr, unittest.mock.AsyncMock())

    return database
"""
def record(cls=None, /, *, new=True):
    """
    @record decorator
    this decorator generates a new __new__ function that
    returns a valid Record instance with the fields
    specified in the decorated class

    This decorator has been inspired by the
    @dataclass decorator
    """

    def wrap(cls):
        return _process_class(cls, new)

    if cls is None:
        # We're called with parens.
        return wrap

    # We're called as @record without parens.
    return wrap(cls)


def _process_class(cls, new):
    if cls.__module__ in sys.modules:
        globals = sys.modules[cls.__module__].__dict__
    else:
        globals = {}

    # Annotated fields defined in this class will be used
    # to generate internal functions
    cls_fields = cls.__dict__.get('__annotations__', {})

    # Now find fields in our class.  While doing so, validate some
    # things, and set the default values (as class attributes) where
    # we can.
    #cls_fields = [field for field in cls_annotations]

    if new:
        # The name to use for the "cls"
        # param in __new__.  Use "cls"
        # if possible.
        cls_name = '__dataclass_cls__' if 'cls' in cls_fields else 'cls'
        self_name = '__dataclass_self__' if 'self' in cls_fields else 'self'

        # create __new__ function that returns a record
        setattr(cls, '__new__', _new_fn(cls_name, cls_fields, globals=globals))
        setattr(cls, '__init__', _init_fn(self_name, cls_fields, globals=globals))

    return cls

def _new_fn(cls_name, fields, *, globals=None):
    """
    create a __new__ function that has cls as first arguemnt
    and fields as required-keyword arguments
    return a Record instance from asyncpg module
    """

    body_lines = []

    body_lines.append("mapping = collections.OrderedDict({" + ", ".join(f"'{f}': {i}" for i, f in enumerate(fields)) + "})")
    body_lines.append('elems = (' + ", ".join(f for f in fields) + ')')
    body_lines.append("return Record(mapping, elems)")

    return _create_fn('__new__', cls_name, fields, body_lines, globals=globals)

def _init_fn(self_name, fields, *, globals=None):
    return _create_fn('__init__', self_name, fields, [], globals=globals)


def _create_fn(name, cls_name, fields, body_lines, *, return_type=None, globals=None):

    if not body_lines:
        body_lines = ["pass"]

    args = ', '.join(f"{field_name}: {field_type.__qualname__}" for (field_name, field_type) in fields.items())
    body = '\n'.join(f'  {b}' for b in body_lines)

    txt = f'def {name}({cls_name}, {args}) -> {return_type}:\n{body}'

    ns = {}
    exec(txt, globals, ns)
    return ns[name]








class MockPool(unittest.mock.MagicMock):
    pass


@record
@dataclass
class MockLeaderboardRecord:
    row_number: int
    author_id: int
    author: str
    sent_total: int


@record
@dataclass
class MockSubjectRecord:
    faculty: str
    code: str
    name: str
    url: str
    terms: List[str]
    created_at: datetime.datetime
    edited_at: Optional[datetime.datetime] = None
    deleted_at: Optional[datetime.datetime] = None


@record
@dataclass
class MockSubjectRegisteredRecord:
    faculty: str
    code: str
    guild_id: int
    member_ids: List[int]


@record
@dataclass
class MockSubjectServerRecord:
    faculty: str
    code: str
    guild_id: int
    category_id: Optional[int]
    channel_id: int
    voice_channel_id: Optional[int]