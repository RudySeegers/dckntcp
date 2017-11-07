import psycopg2

from .config import *


class DbConnection:
    def __init__(self):
        self._conn = psycopg2.connect(host=CONNECTION['HOST'],
                                      database=CONNECTION['DATABASE'],
                                      user=CONNECTION['USER'],
                                      password=CONNECTION['PASSWORD'])

    def connection(self):
        return self._conn


class DbCursor:
    def __init__(self, dbconnection=None):
        if not dbconnection:
            dbconnection = DbConnection()
        self._cur = dbconnection.connection().cursor()

    def execute(self, qry, *args):
        self._cur.execute(qry, (*args,))

    def fetchall(self):
        return self._cur.fetchall()

    def fetchone(self):
        return self._cur.fetchone()

    def execute_and_fetchall(self, qry, *args):
        self.execute(qry, *args)
        return self._cur.fetchall()

    def execute_and_fetchone(self, qry, *args):
        self.execute(qry, *args)
        return self._cur.fetchone()



