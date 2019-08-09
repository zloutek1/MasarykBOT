import sqlite3
import mysql.connector
from mysql.connector.errors import IntegrityError, InterfaceError, OperationalError


class DatabaseConnectionError(InterfaceError):
    pass


def _handle_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except InterfaceError as e:
            if e.errno == 2003:
                raise DatabaseConnectionError(msg=e.msg, errno=e.errno, values=e.args, sqlstate=e.sqlstate) from None

            raise e from None

        except OperationalError as e:
            if e.errno == 2055 or e.msg == "MySQL Connection not available.":
                raise DatabaseConnectionError(msg=e.msg, errno=e.errno, values=e.args, sqlstate=e.sqlstate) from None

            raise e from None

    return wrapper


class Database:
    def __init__(self, db_config={}, conn=None):
        self.conn = conn if conn else None
        self.cursor = None

        if db_config:
            self.conn = _handle_errors(mysql.connector.connect)(**db_config)

    @_handle_errors
    def connect(self):
        if self.conn is None:
            return False

        if not self.conn.is_connected():
            raise DatabaseConnectionError()

        db = Database(conn=self.conn)
        db.cursor = _handle_errors(self.conn.cursor)(dictionary=True)

        db.cursor.execute('SET NAMES utf8mb4')
        db.cursor.execute("SET CHARACTER SET utf8mb4")
        db.cursor.execute("SET character_set_connection=utf8mb4")

        return db

    def __getattrib__(self, attr):
        pass

    def __getattr__(self, attr):
        calling_conn = hasattr(self.conn, attr)
        calling_cursor = hasattr(self.cursor, attr)

        if calling_conn and not calling_cursor:
            return _handle_errors(getattr(self.conn, attr))

        elif calling_cursor and not calling_conn:
            return _handle_errors(getattr(self.cursor, attr))

        elif calling_conn and calling_cursor:
            raise ValueError(f"In {self.__class__} both self.conn and self.cursor have attibute {attr}, please be more specific")

        raise ValueError(f"{self.__class__} has no attribute {attr}")
