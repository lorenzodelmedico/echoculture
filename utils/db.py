import contextlib
import os

import psycopg2


@contextlib.contextmanager
def pg_connection():
    conn = psycopg2.connect(os.environ["POSTGRES_URL"])
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
