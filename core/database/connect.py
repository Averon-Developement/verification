import functools
import pymysql

from core import cfg


def db_connect():
    """
    Create a database connection.
    """
    return pymysql.connect(
        host=cfg.DBHOST,
        port=int(cfg.DBPORT),
        user=cfg.DBUSER,
        password=cfg.DBPASSWORD,
        database=cfg.DBNAME,
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )


def ensure_cursor(func):
    """
    Decorator that provides a database cursor.

    :param func: The function to wrap.
    :return: The wrapped function.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        cursor: pymysql.cursors.Cursor | None = kwargs.get("cursor")
        if cursor:
            return func(*args, **kwargs)

        with db_connect() as conn:
            cursor = conn.cursor()
            kwargs["cursor"] = cursor
            return func(*args, **kwargs)

    return wrapper


def async_ensure_cursor(func):
    """
    Decorator that provides a database cursor for async functions.

    :param func: The coroutine function to wrap.
    :return: The wrapped function.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        cursor: pymysql.cursors.Cursor | None = kwargs.get('cursor')
        if cursor:
            return await func(*args, **kwargs)

        with db_connect() as conn:
            cursor = conn.cursor()
            kwargs['cursor'] = cursor
            return await func(*args, **kwargs)

    return wrapper