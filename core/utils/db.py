import os
import asyncio
import aiomysql
from pymysql.err import OperationalError
from dotenv import load_dotenv
load_dotenv()


class DatabaseConnectionError(OperationalError):
    pass


def _handle_errors(func):
    """
    when database raises an error with a certain error number
    reraise a custom error with a more readable name
    for better code readability
    """
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)

        except OperationalError as e:
            errno = e.args[0]

            if errno == 2003:
                raise DatabaseConnectionError(e.args) from None

            raise e from None

    return wrapper


class Database:
    def __init__(self, conn=None, cursor=None, pool=None):
        self.conn = conn
        self.cursor = cursor
        self.pool = pool

    @classmethod
    @_handle_errors
    async def connect(cls, loop=None):
        """
        establish a database connection based on
        the data set in the .env file
        """

        db = Database()

        if not loop:
            loop = asyncio.get_event_loop()

        pool = await aiomysql.create_pool(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            db=os.getenv("DB_DATABASE"),
            charset="utf8mb4",
            connect_timeout=60,
            loop=loop
        )
        db.pool = pool

        return db

    def __getattr__(self, attr):
        """
        union of unique conn and cursor attributes for
        easier access.

        for example:
            await db.execute calls db.cursor.execute
            await db.commit  calls db.conn.commit

        if the attribute is both in conn and cursor and error
        will be raised to specify which (conn or cursor) was meant
        to be used.
        """

        calling_conn = hasattr(self.conn, attr)
        calling_cursor = hasattr(self.cursor, attr)

        if calling_conn and not calling_cursor:
            return _handle_errors(getattr(self.conn, attr))

        elif calling_cursor and not calling_conn:
            return _handle_errors(getattr(self.cursor, attr))

        elif calling_conn and calling_cursor:
            raise ValueError(
                f"In {self.__class__} both self.conn and self.cursor have attibute {attr}, please be more specific")

        raise ValueError(f"{self.__class__} has no attribute {attr}")
