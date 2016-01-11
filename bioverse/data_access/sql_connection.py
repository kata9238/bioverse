from psycopg2 import connect, Error as PostgresError
from psycopg2.extras import DictCursor

from config import config

#from bioverse_beta.settings import DATABASES


class SQLConnectionHandler(object):
    """Encapsulates the DB connection with the Postgres DB"""
    def __init__(self):
        self._connection = connect(user=config.sql_user,
                                   password=config.sql_password,
                                   database=config.sql_database,
                                   host=config.sql_host,
                                   port=config.sql_port)

    def get_postgres_cursor(self, dictcursor=False):
        """ Returns a Postgres cursor

        Inputs: None

        Returns:
            pgcursor: the postgres.cursor()

        Raises a RuntimeError if the cursor cannot be created
        """
        pgcursor = None
        try:
            if dictcursor:
                pgcursor = self._connection.cursor(cursor_factory=DictCursor)
            else:
                pgcursor = self._connection.cursor()
        except PostgresError, e:
            raise RuntimeError("Cannot get postgres cursor! %s" % str(e))
        return pgcursor

    def _check_sql_args(self, sql_args):
        """ Checks that sql_args have the correct type

        Inputs:
            sql_args: SQL arguments

        Raises a TypeError if sql_args does not have the correct type,
            otherwise it just returns the execution to the caller
        """
        # Check that sql arguments have the correct type
        if sql_args and type(sql_args) not in [tuple, list]:
            raise TypeError("sql_args should be tuple or list. Found %s " %
                            type(sql_args))

    def execute_fetchall(self, sql, sql_args=None, dictcursor=False):
        """ Executes a fetchall SQL query

        Inputs:
            sql: string with the SQL query
            sql_args: tuple with the arguments for the SQL query

        Returns:
            The results of the fetchall query as a list of tuples

        Raises a RuntimeError if there is some error executing the
            SQL query

        Note: from psycopg2 documentation, only variable values should be bound
            via sql_args, it shouldn't be used to set table or field names. For
            those elements, ordinary string formatting should be used before
            running execute.
        """
        # Check that sql arguments have the correct type
        self._check_sql_args(sql_args)
        # Execute the query
        try:
            pgcursor = self.get_postgres_cursor(dictcursor)
            pgcursor.execute(sql, sql_args)
            result = pgcursor.fetchall()
            self._connection.commit()
        except PostgresError, e:
            self._connection.rollback()
            raise RuntimeError("Error running SQL query: %s", str(e))
        finally:
            pgcursor.close()
        return result

    def execute_fetchone(self, sql, sql_args=None, dictcursor=False):
        """ Executes a fetchone SQL query

        Inputs:
            sql: string with the SQL query
            sql_args: tuple with the arguments for the SQL query

        Returns:
            The results of the fetchone query as a tuple

        Raises a RuntimeError if there is some error executing the
            SQL query

        Note: from psycopg2 documentation, only variable values should be bound
            via sql_args, it shouldn't be used to set table or field names. For
            those elements, ordinary string formatting should be used before
            running execute.
        """
        # Check that sql arguments have the correct type
        self._check_sql_args(sql_args)
        # Execute the query
        try:
            pgcursor = self.get_postgres_cursor(dictcursor)
            pgcursor.execute(sql, sql_args)
            result = pgcursor.fetchone()
            self._connection.commit()
        except PostgresError, e:
            self._connection.rollback()
            raise RuntimeError("Error running SQL query: %s", str(e))
        finally:
            pgcursor.close()
        return result

    def execute(self, sql, sql_args=None):
        """ Executes an SQL query with no results

        Inputs:
            sql: string with the SQL query
            sql_args: tuple with the arguments for the SQL query

        Raises a RuntimeError if there is some error executing the
            SQL query

        Note: from psycopg2 documentation, only variable values should be bound
            via sql_args, it shouldn't be used to set table or field names. For
            those elements, ordinary string formatting should be used before
            running execute.
        """
        # Check that sql arguments have the correct type
        self._check_sql_args(sql_args)
        # Execute the query
        try:
            pgcursor = self.get_postgres_cursor()
            pgcursor.execute(sql, sql_args)
            self._connection.commit()
        except PostgresError, e:
            self._connection.rollback()
            raise RuntimeError("Error running SQL query: %s", str(e))
        finally:
            pgcursor.close()

    def executemany(self, sql, sql_args_list):
        """ Executes an executemany SQL query with no results

        Inputs:
            sql: string with the SQL query
            sql_args_list: list with tuples with the arguments for the SQL
                query

        Raises a RuntimeError if there is some error executing the
            SQL query

        Note: from psycopg2 documentation, only variable values should be bound
            via sql_args, it shouldn't be used to set table or field names. For
            those elements, ordinary string formatting should be used before
            running execute.
        """
        # Check that sql arguments have the correct type
        for sql_args in sql_args_list:
            self._check_sql_args(sql_args)
        # Execute the query
        try:
            pgcursor = self.get_postgres_cursor()
            pgcursor.executemany(sql, sql_args_list)
            self._connection.commit()
        except PostgresError, e:
            self._connection.rollback()
            raise RuntimeError("Error running SQL query: %s", str(e))
        finally:
            pgcursor.close()
