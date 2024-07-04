import sqlite3

from src.services.swit_schemas import SwitTokens

_DB_NAME = 'service_accounts.db'
_TABLE_NAME = 'service_accounts'
_SERVICE_ACCOUNT = 'service_account'


def _get_db() -> sqlite3.Connection:
    return sqlite3.connect(_DB_NAME)


def close_db(db: sqlite3.Connection) -> None:
    if db is not None:
        db.close()


def init_db() -> None:
    with _get_db() as db:
        c = db.cursor()
        c.execute(f'''
        CREATE TABLE IF NOT EXISTS {_TABLE_NAME} (
            username VARCHAR(30) PRIMARY KEY,
            access_token TEXT NOT NULL,
            refresh_token TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')


def upsert_service_account(tokens: SwitTokens) -> None:
    with _get_db() as db:
        c = db.cursor()
        c.execute(f'''
        INSERT INTO {_TABLE_NAME} (username, access_token, refresh_token)
        VALUES (?, ?, ?)
        ON CONFLICT(username) DO UPDATE
        SET access_token = EXCLUDED.access_token,
            refresh_token = EXCLUDED.refresh_token,
            updated_at = CURRENT_TIMESTAMP
        ''', (
            _SERVICE_ACCOUNT, tokens.access_token, tokens.refresh_token))


def get_service_account() -> SwitTokens:
    with _get_db() as db:
        c = db.cursor()
        c.execute(f"SELECT access_token, refresh_token FROM {_TABLE_NAME} WHERE username = '{_SERVICE_ACCOUNT}'")
        res = c.fetchone()
    if not res:
        raise Exception("Service account not found")
    return SwitTokens(access_token=res[0], refresh_token=res[1])
