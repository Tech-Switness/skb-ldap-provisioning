""" database model """
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()

class SwitUserToken(BaseModel):
    """ swit user token (bot user)"""
    __tablename__ = 'swit_admin_token'

    token_id = Column(Integer, primary_key=True, nullable=False)
    access_token = Column(String(500), nullable=False)
    refresh_token = Column(String(500), nullable=False)

    def __init__(
        self,
        access_token: str,
        refresh_token: str,
        token_id: int = 1
    ):
        self.token_id = token_id
        self.access_token = access_token
        self.refresh_token = refresh_token

    def __repr__(self):
        return f"SwitUserToken(token_id={self.token_id!r},access_token={self.access_token!r},refresh_token={self.refresh_token!r})"
