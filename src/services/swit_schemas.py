import re
from enum import IntEnum

from typing import Optional, Annotated
from pydantic import BaseModel, Field, ConfigDict, AfterValidator

from src.core.constants import settings


class SwitUserRoleEnum(IntEnum):
    MASTER = 10
    ADMIN = 20
    MEMBER = 30
    GUEST = 40


class SwitUser(BaseModel):
    """A class to hold team information"""
    model_config = ConfigDict(populate_by_name=True, extra='ignore')

    id: str = Field(..., alias='user_id')
    name: str = Field(..., alias='user_name')
    email: str
    phone_number: Annotated[str,
    AfterValidator(lambda v: re.sub(r'[^0-9+-]', '', v)),
    Field(..., alias='tel')]
    timezone: str
    language: str
    is_active: bool
    role: SwitUserRoleEnum


class SwitUserRequest(BaseModel):
    """A class when used to create a Swit user"""
    model_config = ConfigDict(populate_by_name=True, extra='forbid')

    name: str = Field(..., alias='user_name')
    email: str = Field(..., alias='user_email')
    phone_number: Optional[str] = Field(None, alias='tel')
    language: str = settings.DEFAULT_USER_LANGUAGE


class SwitTeam(BaseModel):
    """A class to hold Swit team information"""
    model_config = ConfigDict(populate_by_name=True, strict=True, extra='ignore')

    id: str = Field(..., alias='team_id')
    name: str = Field(..., alias='team_name')
    parent_id: str = Field(..., alias='parent_id')
    ref_id: Optional[str] = Field(None, alias='reference')
    user_ids: list[str] = Field([], alias='users')


class SwitTeamRequest(BaseModel):
    """A class when used to update or create a Swit team"""
    model_config = ConfigDict(populate_by_name=True, strict=True, extra='forbid')

    id: Optional[str] = Field(None)
    name: Optional[str] = Field(None)
    parent_id: Optional[str] = Field(None)
    ref_id: Optional[str] = Field(None, alias='reference')


class SwitTokens(BaseModel):
    """A class to hold Swit token information"""
    model_config = ConfigDict(populate_by_name=True, strict=True, extra='ignore')

    access_token: str
    refresh_token: str
