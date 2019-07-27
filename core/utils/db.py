import mysql.connector
from mysql.connector.errors import IntegrityError, InterfaceError


class Database:
    def __init__(self):
        self.conn = None
        self.cursor = None

    @classmethod
    def connect(cls, *args, **kwargs):
        db = Database()
        db.conn = mysql.connector.connect(*args, **kwargs)
        db.cursor = db.conn.cursor(dictionary=True)

        return db

    def __getattrib__(self, attr):
        pass

    def __getattr__(self, attr):
        calling_conn = hasattr(self.conn, attr)
        calling_cursor = hasattr(self.cursor, attr)

        if calling_conn and not calling_cursor:
            return getattr(self.conn, attr)

        elif calling_cursor and not calling_conn:
            return getattr(self.cursor, attr)

        elif calling_conn and calling_cursor:
            raise ValueError(f"In {self.__class__} both self.conn and self.cursor have attibute {attr}, please be more specific")

        raise ValueError(f"{self.__class__} has no attribute {attr}")
