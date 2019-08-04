import mysql.connector
from mysql.connector.errors import IntegrityError, InterfaceError


class DatabaseConnectionError(InterfaceError):
    pass


class Database:
    def __init__(self):
        self.conn = None
        self.cursor = None

    @classmethod
    def connect(cls, *args, **kwargs):
        if args or kwargs:
            db = Database()
            db.conn = cls._handle_errors(mysql.connector.connect)(*args, **kwargs)
            db.cursor = db.conn.cursor(dictionary=True)

            return db

    @staticmethod
    def _handle_errors(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except InterfaceError as e:
                if e.errno == 2003:
                    raise DatabaseConnectionError(msg=e.msg, errno=e.errno, values=e.args, sqlstate=e.sqlstate) from None
                raise e from None
        return wrapper

    def __getattrib__(self, attr):
        pass

    def __getattr__(self, attr):
        calling_conn = hasattr(self.conn, attr)
        calling_cursor = hasattr(self.cursor, attr)

        if calling_conn and not calling_cursor:
            return self._handle_errors(getattr(self.conn, attr))

        elif calling_cursor and not calling_conn:
            return self._handle_errors(getattr(self.cursor, attr))

        elif calling_conn and calling_cursor:
            raise ValueError(f"In {self.__class__} both self.conn and self.cursor have attibute {attr}, please be more specific")

        raise ValueError(f"{self.__class__} has no attribute {attr}")
