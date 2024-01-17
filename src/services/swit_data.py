from collections import Counter
from enum import IntEnum

from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict

from src.core.constants import DEFAULT_USER_LANGUAGE, DEFAULT_USER_TIMEZONE
from src.services.swit_api_client import authenticated_requests


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


def get_existing_swit_users() -> dict[str, SwitUser]:
    """Get existing swit users"""
    # Request for all users
    page = 0
    swit_users = []
    while True:
        page += 1
        res = authenticated_requests('GET', '/organization.user.list', params={
            'cnt': 1000,
            'page': page,
        }, timeout=10)
        new_users = res.json()['data']['users']
        if not new_users:
            break
        swit_users += new_users

    # Map swit users by email
    swit_users_by_email = {
        user_json['email']: SwitUser(**user_json)
        for user_json in swit_users
    }
    return swit_users_by_email


def get_existing_swit_teams() -> tuple[dict[str, SwitTeam], list[SwitTeam], str]:
    """Get existing swit teams"""
    res = authenticated_requests('GET', '/user.team.list', timeout=10)
    raw_swit_teams: list[dict[str, Any]] = res.json()['data']['team']
    root_team_id = next(team['team_id'] for team in raw_swit_teams if team['depth'] == 0)
    all_swit_teams = [SwitTeam(**team_json) for team_json in raw_swit_teams]

    # ATTENTION: Assert that all ref_ids are unique
    ref_ids = [team.ref_id for team in all_swit_teams if team.ref_id]
    counter = Counter(ref_ids)
    duplicates = [ref_id for ref_id, count in counter.items() if count > 1]
    assert not duplicates, f'Duplicated ref_id(s) from Swit: {duplicates}'

    # ATTENTION: Exclude the root team and 'Unassigned' team
    #  because they're not actual teams
    all_swit_teams = [team for team in all_swit_teams
                      if team.id != root_team_id and team.name != 'Unassigned']
    swit_teams_by_ref = {
        swit_team.ref_id: swit_team
        for swit_team in all_swit_teams if swit_team.ref_id
    }
    return swit_teams_by_ref, all_swit_teams, root_team_id
