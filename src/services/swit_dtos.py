from enum import IntEnum

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from src.core.constants import DEFAULT_USER_LANGUAGE, DEFAULT_USER_TIMEZONE


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
    phone_number: str = Field(..., alias='tel')
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
    timezone: str = Field(DEFAULT_USER_TIMEZONE)
    language: str = Field(DEFAULT_USER_LANGUAGE)


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
