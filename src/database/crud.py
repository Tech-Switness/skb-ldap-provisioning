""" database CRUD API """
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

# from src.setting import config
from . import connect
from . import model

engine = connect.connect_sql()
model.base_model.metadata.create_all(engine)

sessionLocal = sessionmaker(engine)

def get_db_session():
    """ create database local session """
    db_session = sessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

# swit bot user token
def get_swit_user_token(
    db_session: Session,
    token_id: int = 1
):
    """ get swit user token record from cloud sql """
    stmt = select(model.SwitUserToken).where(model.SwitUserToken.token_id == token_id)
    return db_session.scalar(stmt)

def insert_swit_user_token(
    db_session: Session,
    swit_user_id: str,
    access_token: str,
    refresh_token: str,
    token_id: int = 1
):
    """ insert swit user token """
    if get_swit_user_token(db_session, token_id):
        update_swit_user_token(
            db_session,
            token_id,
            swit_user_id=swit_user_id,
            access_token=access_token,
            refresh_token=refresh_token
        )
        return

    swit_user_token = model.SwitUserToken(
        swit_user_id,
        access_token,
        refresh_token
    )
    db_session.add(swit_user_token)

    db_session.commit()

def update_swit_user_token(
    db_session: Session,
    token_id: int = 1,
    swit_user_id: str = "",
    access_token: str = "",
    refresh_token: str = "",
):
    """ update swit user token """
    swit_user_token = get_swit_user_token(db_session, token_id)
    if swit_user_id:
        swit_user_token.swit_user_id = swit_user_id
    if access_token:
        swit_user_token.access_token = access_token
    if refresh_token:
        swit_user_token.refresh_token = refresh_token

    db_session.commit()
