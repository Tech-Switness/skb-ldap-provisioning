""" database model """
from sqlalchemy import Column, String, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base

base_model = declarative_base()

class SwitUserToken(base_model):
    """ swit user token (bot user)"""
    __tablename__ = 'swit_user_token'

    token_id = Column(Integer, primary_key=True, nullable=False)
    swit_user_id = Column(String(50), nullable=False)
    access_token = Column(String(500), nullable=False)
    refresh_token = Column(String(500), nullable=False)
    in_usage = Column(Boolean, nullable=False)

    def __init__(
        self,
        swit_user_id: str,
        access_token: str,
        refresh_token: str,
        in_usage: bool = False,
        token_id: int = 1
    ):
        self.token_id = token_id
        self.swit_user_id = swit_user_id
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.in_usage = in_usage

    def __repr__(self):
        return f"SwitUserToken(token_id={self.token_id!r},swit_user_id={self.swit_user_id!r},access_token={self.access_token!r},refresh_token={self.refresh_token!r},in_usage={self.in_usage!r})"
