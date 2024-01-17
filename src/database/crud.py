""" database CRUD API """
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

# from src.setting import config
from . import connect
from . import models

engine = connect.connect_sql()
models.BaseModel.metadata.create_all(engine)

sessionLocal = sessionmaker(engine)

def get_db_session():
    """ create database local session """
    db_session = sessionLocal()
    try:
        return db_session
    finally:
        db_session.close()

def close_db_session(db_session: Session):
    """ close database local session """
    db_session.close()

# swit services user token
def get_swit_user_token(
    db_session: Session,
    token_id: int = 1
):
    """ get swit user token record from cloud sql """
    statement = select(models.SwitUserToken).where(models.SwitUserToken.token_id == token_id)
    return db_session.scalar(statement)

def insert_swit_user_token(
    db_session: Session,
    access_token: str,
    refresh_token: str,
    token_id: int = 1
):
    """ insert swit user token """
    if get_swit_user_token(db_session, token_id):
        update_swit_user_token(
            db_session,
            token_id,
            access_token=access_token,
            refresh_token=refresh_token
        )
        return

    swit_user_token = model.SwitUserToken(
        access_token,
        refresh_token
    )
    db_session.add(swit_user_token)

    db_session.commit()

def update_swit_user_token(
    db_session: Session,
    token_id: int = 1,
    access_token: str = "",
    refresh_token: str = "",
):
    """ update swit user token """
    swit_user_token = get_swit_user_token(db_session, token_id)
    if access_token:
        swit_user_token.access_token = access_token
    if refresh_token:
        swit_user_token.refresh_token = refresh_token

    db_session.commit()
