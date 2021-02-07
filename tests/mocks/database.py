import collections
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

    def wrapper(**kwargs):
        """
        require all key-word arguments to be filled and have required type
        """
        missing = []
        for i, (field, ftype) in enumerate(func.__annotations__.items()):
            if field not in kwargs:
                missing.append(field)
            elif not isinstance(kwargs[field], ftype):
                raise TypeError(f"Couldn't match expected type {ftype} with actual type {type(kwargs[field])} in {pos(i+1)} argument {field}")
        if missing:
            raise TypeError(f"{func.__qualname__} missing {len(missing)} required keyword-only arguments: {', '.join(missing)}")

        elems = tuple(kwargs.values())
        return Record(mapping, elems)
    return wrapper

@record
def MockLeaderboardRecord(*, row_number: int, author_id: int, author: str, sent_total: int):
    pass