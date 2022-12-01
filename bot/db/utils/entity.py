from asyncpg import Record



class Entity:
    __table_name__: str


    @classmethod
    def convert(cls, record: Record) -> "Entity":
        # noinspection PyArgumentList
        return cls(**{k: v for (k, v) in record.items()})

