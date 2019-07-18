import mysql.connector
from mysql.connector.errors import IntegrityError


class DuplicateEntryError(IntegrityError):
    pass


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

    def execute(self, *args, **kwargs):
        try:
            self.cursor.execute(*args, **kwargs)
        except IntegrityError as e:
            if e.errno == 1062:
                raise DuplicateEntryError(msg=e.msg, errno=e.errno, values=e.args, sqlstate=e.sqlstate)
            raise e

    def executemany(self, *args, **kwargs):
        try:
            self.cursor.executemany(*args, **kwargs)
        except IntegrityError as e:
            if e.errno == 1062:
                raise DuplicateEntryError(msg=e.msg, errno=e.errno, values=e.args, sqlstate=e.sqlstate)
            raise e

    def fetchone(self, *args, **kwargs):
        return self.cursor.fetchone(*args, **kwargs)

    def fetchall(self, *args, **kwargs):
        return self.cursor.fetchall(*args, **kwargs)

    def commit(self, *args, **kwargs):
        self.conn.commit(*args, **kwargs)
