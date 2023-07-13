""" google cloud sql 연결 """
import os

import pymysql
import sqlalchemy

def connect_sql() -> sqlalchemy.engine.base.Engine:
    """ connect sql """
    return connect_with_connector()

def connect_with_connector() -> sqlalchemy.engine.base.Engine:
    """ sqlalchemy engine 가져오기 """

    db_user = os.getenv("DB_USERNAME")
    db_pass = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")

    # Define the MySQL URL
    url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    # Create the SQLAlchemy engine
    engine = sqlalchemy.create_engine(
        url,
        # Pool size is the maximum number of permanent connections to keep.
        pool_size=30,
        # Temporarily exceeds the set pool_size if no connections are available.
        max_overflow=30,
        # The total number of concurrent connections for your application will be
        # a total of pool_size and max_overflow.
        # 'pool_timeout' is the maximum number of seconds to wait when retrieving a
        # new connection from the pool. After the specified amount of time, an
        # exception will be thrown.
        pool_timeout=30,  # 30 seconds
        # 'pool_recycle' is the maximum number of seconds a connection can persist.
        # Connections that live longer than the specified amount of time will be
        # re-established
        pool_recycle=1800,  # 30 minutes
    )

    return engine
