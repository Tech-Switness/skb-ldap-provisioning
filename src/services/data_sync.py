""" import directory data via ldap """
import time
import re
from collections import Counter

from typing import Any

from httpx import HTTPStatusError

from src.core.constants import settings
from src.services.idp_data import import_idp_users, import_idp_teams
from src.services.swit_api_client import SwitApiClient
from src.services.swit_schemas import SwitTeam, SwitUser, \
    SwitTeamRequest, SwitUserRoleEnum, SwitUserRequest
from src.core.logger import provisioning_logger as logger, SwitWebhookBufferingHandler

# ATTENTION: To avoid rate limiting, we sleep for a short time after each API call
_SLEEP_TIME = 0.2


def sync_to_swit() -> None:
    """
    Syncs data from the IdP to Swit.
    """
    try:
        print("Starting data sync from the IdP to Swit in a separate thread...")
        SyncUsers()
        SyncTeams()
    except Exception as e:
        logger.exception(e)
    finally:
        for handler in logger.handlers:
            if isinstance(handler, SwitWebhookBufferingHandler):
                handler.flush()
        print("Data sync completed.")


class Sync:
    def __init__(self) -> None:
        self._api_client = SwitApiClient()

    def _get_existing_swit_users(self) -> dict[str, SwitUser]:
        """Get existing swit users"""
        # Request for all users
        page = 0
        swit_users = []
        while True:
            page += 1
            res = self._api_client.get(
                '/organization.user.list',
                params={
                    'cnt': 1000,
                    'page': page,
                })
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


class SyncUsers(Sync):
    """
    Syncs user data from the IdP to Swit.
    """

    def __init__(self) -> None:
        super().__init__()
        self._idp_users = import_idp_users()
        self._create_and_update()

        # TODO
        """ SKB는 현재 IdP 기준으로 활성 여부를 제어하고 있지 않음
        self._update_active_status()
        """

    def _create_and_update(self) -> None:
        print("Syncing users...")
        # Fetching existing data from Swit
        swit_users_by_email = self._get_existing_swit_users()
        for idp_user in self._idp_users:
            swit_user = swit_users_by_email.get(idp_user.email)

            # TODO
            """ SKB는 이 기능을 사용하는 대신 SSO를 통해 회원 가입
            # Create a new user if it doesn't exist on Swit
            if not swit_user:
                username = _clean_string(idp_user.name)
                self._api_client.post(
                    '/organization.user.create',
                    json=SwitUserRequest(
                        name=username,
                        email=idp_user.email,
                        phone_number=idp_user.phone_number,
                    ).model_dump(exclude_none=True, by_alias=True))
                logger.info(f"Created user: {username}")
                time.sleep(_SLEEP_TIME)
                continue

            # Activate the user if inactive
            if not swit_user.is_active:
                self._api_client.post('/organization.user.activate',
                                      json={'id': swit_user.id})
                logger.info(f"Activated user: {swit_user.name}")
                time.sleep(_SLEEP_TIME)
            """
            if not swit_user:
                continue

            # TODO: Replace the SCIM API with the new API when it's ready
            operations = []
            if _clean_string(idp_user.name) != swit_user.name:
                operations.append({
                    "op": "Replace",
                    "path": "displayName",
                    "value": _clean_string(idp_user.name)
                })
            if idp_user.phone_number != swit_user.phone_number:
                operations.append({
                    "op": "Replace",
                    "path": "phoneNumbers[type eq \"mobile\"].value",
                    "value": idp_user.phone_number
                })
            if not operations:
                continue

            self._api_client.patch(
                f"https://saml.swit.io/scim/v2/Users/{swit_user.id}",
                json={
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                    "Operations": operations
                }
            )
            logger.info(f"Updated user: {_clean_string(idp_user.name)}")
            time.sleep(_SLEEP_TIME)

    def _update_active_status(self) -> None:
        print("Updating user active status...")
        swit_users_by_email = self._get_existing_swit_users()
        active_swit_user_emails = {swit_user.email for swit_user
                                   in swit_users_by_email.values()
                                   if swit_user.is_active}
        idp_user_emails = {idp_user.email for idp_user in self._idp_users}

        # Deactivate users who are active on Swit but not on IdP
        user_emails_to_deactivate = active_swit_user_emails - idp_user_emails
        for email in user_emails_to_deactivate:
            swit_user = swit_users_by_email[email]
            if swit_user.role == SwitUserRoleEnum.MASTER \
                    or swit_user.role == SwitUserRoleEnum.ADMIN:
                # ATTENTION: Do not deactivate admins
                continue
            if not settings.IS_RUNNING_LOCALLY:
                # TODO when using test data, unintended deactivation can occur
                self._api_client.post('/organization.user.deactivate',
                                      json={'user_id': swit_user.id})
            logger.info(f"Deactivated user: {swit_user.name}")
            time.sleep(_SLEEP_TIME)

        # Activate users who are active on IdP but not active on Swit
        user_emails_to_activate = idp_user_emails - active_swit_user_emails
        for email in user_emails_to_activate:
            if email not in swit_users_by_email:
                # In case the user does not exist on Swit
                continue
            swit_user = swit_users_by_email[email]
            self._api_client.post('/organization.user.activate',
                                  json={'user_id': swit_user.id})
            logger.info(f"Activated user: {swit_user.name}")
            time.sleep(_SLEEP_TIME)


class SyncTeams(Sync):
    """
    Syncs team data from the IdP to Swit.
    """

    def __init__(self) -> None:
        super().__init__()
        self._idp_teams = import_idp_teams()
        self._remove_unused()
        self._create()
        self._update()
        self._sort()

    def _remove_unused(self) -> None:
        print("Removing unused teams...")
        swit_teams_by_ref, all_swit_teams, root_team_id = self._get_existing_swit_teams()
        idp_team_ref_ids = {team.ref_id for team in self._idp_teams}
        for swit_team in all_swit_teams:
            if swit_team.ref_id in idp_team_ref_ids:
                # If the team is in IdP
                continue
            try:
                self._api_client.post('/team.delete',
                                      json={'id': swit_team.id})
            except HTTPStatusError as e:
                # If the team has already been deleted
                print(123, swit_team, e)
                logger.info(f"Team {swit_team.name} has already been deleted")
                pass
            time.sleep(_SLEEP_TIME)

    def _create(self) -> None:
        print("Creating teams...")
        swit_teams_by_ref, all_swit_teams, root_team_id = self._get_existing_swit_teams()
        for idp_team in self._idp_teams:
            # Create a new one if it doesn't exist on Swit
            if idp_team.ref_id not in swit_teams_by_ref:
                res = self._api_client.post(
                    '/team.create',
                    json=SwitTeamRequest(
                        name=_get_unique_team_name(idp_team.name, all_swit_teams),
                        ref_id=idp_team.ref_id,
                        parent_id=root_team_id
                    ).model_dump(exclude_none=True, by_alias=True))
                new_swit_team = SwitTeam.model_validate(res.json()['data'])
                logger.info(f"Created team: {new_swit_team.name}")
                swit_teams_by_ref[idp_team.ref_id] = new_swit_team
                all_swit_teams.append(new_swit_team)
                time.sleep(_SLEEP_TIME)

    def _update(self) -> None:
        """
        Keep swit teams are up-to-date
        Unlike users, team updates must be done after all teams are created
        because they can refer to each other
        """
        print("Updating teams...")
        swit_teams_by_ref, all_swit_teams, root_team_id = self._get_existing_swit_teams()
        swit_users_by_email = self._get_existing_swit_users()
        for idp_team in self._idp_teams:
            swit_team = swit_teams_by_ref.get(idp_team.ref_id)
            if swit_team is None:
                continue

            # Collect fields to update to minimize API calls
            fields_to_update = {}

            # Update team name
            if _clean_string(swit_team.name) != _clean_string(idp_team.name):
                fields_to_update['name'] = _get_unique_team_name(idp_team.name, all_swit_teams)

            # Update parent team
            new_parent_swit_team_id: str = root_team_id
            if idp_team.parent_ref_id:
                parent_swit_team = swit_teams_by_ref.get(idp_team.parent_ref_id)
                if parent_swit_team:
                    new_parent_swit_team_id = parent_swit_team.id

            if new_parent_swit_team_id != swit_team.parent_id:
                fields_to_update['parent_id'] = new_parent_swit_team_id

            # Update team info if necessary
            if fields_to_update:
                self._api_client.post(
                    '/team.update',
                    json=SwitTeamRequest(
                        id=swit_team.id,
                        **fields_to_update
                    ).model_dump(exclude_none=True, by_alias=True))
                logger.info(f"Updated team: {swit_team.name}")
                time.sleep(_SLEEP_TIME)

            # Check that team members are up-to-date
            swit_team_user_ids = set(swit_team.user_ids)
            idp_team_user_ids = {swit_users_by_email[idp_user.email].id
                                 for idp_user in idp_team.users
                                 if idp_user.email in swit_users_by_email}

            # Add members
            members_to_add = idp_team_user_ids - swit_team_user_ids
            if members_to_add:
                self._api_client.post(
                    '/team.user.add',
                    json={
                        'id': swit_team.id,
                        'user_ids': list(members_to_add)
                    })
                logger.info(f"Added {len(members_to_add)} members to team: {swit_team.name}")
                time.sleep(_SLEEP_TIME)

            # remove members
            members_to_remove = swit_team_user_ids - idp_team_user_ids
            if members_to_remove:
                self._api_client.post(
                    '/team.user.remove',
                    json={
                        'id': swit_team.id,
                        'user_ids': list(members_to_remove)
                    })
                logger.info(f"Removed {len(members_to_remove)} members from team: {swit_team.name}")
                time.sleep(_SLEEP_TIME)

    def _sort(self) -> None:
        print("Sorting teams...")
        swit_teams_by_ref, all_swit_teams, _ = self._get_existing_swit_teams()
        for idp_team in self._idp_teams:
            swit_team = swit_teams_by_ref.get(idp_team.ref_id)
            if swit_team is None:
                continue
            # Find children of the team
            idp_team_child_ids = [team.ref_id for team in self._idp_teams if team.parent_ref_id == idp_team.ref_id]
            swit_team_children = [team for team in all_swit_teams if team.parent_id == swit_team.id]

            def _sort_children(target_team: SwitTeam) -> int:
                target_team_ref_id = target_team.ref_id
                if target_team_ref_id and target_team_ref_id in idp_team_child_ids:
                    primary_order = idp_team_child_ids.index(target_team_ref_id)
                else:
                    # If the id is not in all_ids, set primary_order to a large number
                    primary_order = len(idp_team_child_ids)
                return primary_order

            swit_team_children_sorted = sorted(swit_team_children, key=_sort_children)
            if not any(o1 != o2 for o1, o2 in zip(swit_team_children, swit_team_children_sorted)):
                # If the children are already sorted
                continue
            self._api_client.post(
                '/team.sort',
                json={
                    'parent_id': swit_team.id,
                    'team_ids': [team.id for team in swit_team_children_sorted]
                })
            logger.info(f"Sorted team: {swit_team.name}")
            time.sleep(_SLEEP_TIME)

    def _get_existing_swit_teams(self) -> tuple[dict[str, SwitTeam], list[SwitTeam], str]:
        """Get existing swit teams"""
        res = self._api_client.get('/user.team.list')
        raw_swit_teams: list[dict[str, Any]] = res.json()['data']['team']
        root_team_id = next(team['team_id'] for team in raw_swit_teams if team['depth'] == 0)
        all_swit_teams = [SwitTeam.model_validate(team_json) for team_json in raw_swit_teams]

        # ATTENTION: Ensure that all ref_ids are unique
        ref_ids = [team.ref_id for team in all_swit_teams if team.ref_id]
        counter = Counter(ref_ids)
        duplicates = [ref_id for ref_id, count in counter.items() if count > 1]
        deleted_team_ids = []
        for duplicate in duplicates:
            duplicate_teams = [team for team in all_swit_teams if team.ref_id == duplicate]
            # Keep the team with the most members
            duplicate_teams.sort(key=lambda team: len(team.user_ids), reverse=True)
            for team in duplicate_teams[1:]:
                try:
                    self._api_client.post('/team.delete',
                                          json={'id': team.id})
                except HTTPStatusError:
                    pass
                deleted_team_ids.append(team.id)

        # ATTENTION: Exclude the root team and 'Unassigned' team
        #  because they're not actual teams
        all_swit_teams = [team for team in all_swit_teams
                          if team.id != root_team_id and team.name != 'Unassigned'
                          and team.id not in deleted_team_ids]
        swit_teams_by_ref = {
            swit_team.ref_id: swit_team
            for swit_team in all_swit_teams if swit_team.ref_id
        }
        return swit_teams_by_ref, all_swit_teams, root_team_id


def _get_unique_team_name(team_name: str, all_swit_teams: list[SwitTeam]) -> str:
    """
    ATTENTION: Get a unique team name by adding a number suffix. Be aware that:
      1. Duplicate team names are not allowed on Swit.
      2. Duplicates must be checked case-insensitively.
    """
    cleaned_team_name = _clean_string(team_name)
    # Be aware that the Swit API is case-insensitive
    existing_team_names = {team.name.lower() for team in all_swit_teams}
    if cleaned_team_name.lower() not in existing_team_names:
        return cleaned_team_name
    for i in range(2, 100):
        new_team_name = f"{cleaned_team_name} ({i})"
        if new_team_name.lower() not in existing_team_names:
            return new_team_name
    raise RuntimeError(f"Failed to generate a unique team name for {team_name}")


def _clean_string(string: str) -> str:
    """
    ATTENTION: Replace @ # < > § ▒ { } ; * with underscore in the string
        and remove duplicated number suffixes
    """
    string = re.sub(r'[@#<>§▒{};*]', '_', string)
    # Remove duplicated number suffixes
    string = re.sub(r' \([0-9]+\)$', '', string)
    return string.strip()
