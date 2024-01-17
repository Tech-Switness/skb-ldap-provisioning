""" google cloud sql 연결 """
import sqlalchemy

from src.core.constants import DB_USERNAME, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME


def connect_sql() -> sqlalchemy.engine.base.Engine:
    """ connect sql """
    return connect_with_connector()


def connect_with_connector() -> sqlalchemy.engine.base.Engine:
    """ sqlalchemy engine 가져오기 """

    # Define the MySQL URL
    url = (f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}"
           f"@{DB_HOST}:{DB_PORT}/{DB_NAME}")

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
