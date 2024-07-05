import json
import re
from typing import Optional, TypedDict

from pydantic import BaseModel

from src.core.constants import settings
from src.services.ldap_connection import connect_ldap, LdapSettings


class IdpUser(BaseModel):
    """A class to hold IdP user information"""
    ref_id: str
    name: str
    email: str
    phone_number: str


class IdpTeam(BaseModel):
    """A class to hold IdP team information"""
    ref_id: str
    name: str
    parent_ref_id: Optional[str]
    users: list[IdpUser]


class RawIdpUser(TypedDict):
    distinguishedName: str
    mail: str
    displayName: str
    mobile: Optional[str]


class RawIdpTeam(TypedDict):
    member: list[str]
    memberOf: list[str]
    distinguishedName: str
    displayName: str


def import_idp_users() -> list[IdpUser]:
    """Import users from IdP"""
    raw_idp_users: list[RawIdpUser] = []

    if settings.IS_RUNNING_LOCALLY:
        with open('fixtures/ldap_test_data.json') as f:
            raw_idp_users = json.load(f)['users']
    else:
        with connect_ldap() as conn:
            ldap_settings = LdapSettings()
            for ou in ldap_settings.LDAP_USER_OUS.split(','):
                conn.search(
                    search_base=f'OU={ou},{ldap_settings.LDAP_SEARCH_BASE}',
                    search_filter='(objectclass=*)',
                    attributes=['distinguishedName', 'mail', 'displayName', 'mobile']
                )
                assert conn.response is not None, f'No response from the IdP for OU: {ou}'
                raw_idp_users += [e['attributes'] for e in conn.response]

    return [IdpUser(
        ref_id=raw_user['distinguishedName'],
        name=raw_user['displayName'],
        email=raw_user['mail'],
        phone_number=raw_user.get('mobile') or ''
    ) for raw_user in raw_idp_users if raw_user['mail']]


def import_idp_teams() -> list[IdpTeam]:
    """Import teams from IdP"""
    idp_users = import_idp_users()
    idp_users_by_ref_id = {idp_user.ref_id: idp_user for idp_user in idp_users}

    raw_idp_teams: list[RawIdpTeam] = []

    if settings.IS_RUNNING_LOCALLY:
        with open('fixtures/ldap_test_data.json') as f:
            raw_idp_teams = json.load(f)['groups']
    else:
        with connect_ldap() as conn:
            ldap_settings = LdapSettings()
            for ou in ldap_settings.LDAP_GROUP_OUS.split(','):
                conn.search(
                    search_base=f'OU={ou},{ldap_settings.LDAP_SEARCH_BASE}',
                    search_filter='(objectclass=*)',
                    attributes=['distinguishedName', 'member', 'memberOf', 'displayName']
                )
                assert conn.response is not None, f'No response from the IdP for OU: {ou}'
                raw_idp_teams += [e['attributes'] for e in conn.response]

    return [IdpTeam(
        ref_id=raw_team['distinguishedName'],
        name=raw_team['displayName'],
        parent_ref_id=(raw_team['memberOf'][0]
                       if raw_team['memberOf'] else None),
        users=[idp_users_by_ref_id[user_ref_id] for user_ref_id
               in raw_team['member']
               if user_ref_id in idp_users_by_ref_id]
    ) for raw_team in raw_idp_teams
        if not _check_for_exclusion(raw_team['distinguishedName'])
    ]


_teams_to_exclude = set(settings.TEAMS_TO_EXCLUDE.split(','))


def _check_for_exclusion(distinguished_name: str) -> bool:
    pattern = re.compile(r"CN=([^,]+)")
    matches = pattern.findall(distinguished_name)
    return len(set(matches) & _teams_to_exclude) > 0
