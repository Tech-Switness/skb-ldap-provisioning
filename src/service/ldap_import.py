""" import directory data via ldap """
import os
import time
import re
import ssl
import json

import requests
from ldap3 import Server, Connection, SYNC, Tls, SIMPLE, ALL

from . import auth

TEAMS_TO_EXCLUDE = []
class Team:
    '''team class'''
    def __init__(self, distinguished_name: str, parent: str, members: list, display_name: str):
        self.distinguished_name = distinguished_name
        self.parent = parent
        self.members = members
        self.display_name = display_name

def replace_special_characters(string):
    '''replace special characters'''
    return re.sub(r'[^\w()&\s_-]', '_', string)

def send_webhook(msg_list: str):
    """ send webhook message """
    webhook_url = "YOUR_WEBHOOK_URL"
    log_msg = {
        "text": "\n".join(msg_list)
    }
    res = requests.post(webhook_url, json=log_msg, timeout=10)
    print(res.json())

def make_request(
    method,
    path,
    retry_after=1,
    base_url="https://openapi.swit.io/v1/api",
    **kwargs
):
    '''make request to swit api'''
    if method not in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
        raise ValueError('Unsupported HTTP method')

    headers = { # prod
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('SWIT_ACCESS_TOKEN')}"
    }

    try:
        res = requests.request(method, base_url+path, headers=headers, **kwargs)
        time.sleep(0.5)
        if res.status_code == 401: # token expire
            auth.token_refresh()
            send_webhook(["token refresh"])
            res = make_request(method, path, retry_after, **kwargs)

        if res.status_code == 429:
            err_msg_list = []
            err_msg_list.append(json.dumps(res.json()))
            err_msg_list.append(json.dumps(kwargs))
            # Wait the specified number of seconds
            err_msg_list.append(f'Retry: {retry_after}')
            send_webhook(err_msg_list)
            time.sleep(retry_after)
            # Make the request again
            if retry_after < 5:
                res = make_request(method, path, retry_after+1, **kwargs)
        return res
    except requests.exceptions.ConnectionError as err:
        err_msg_list = []
        err_msg_list.append(str(err))
        err_msg_list.append(f'Retry: {retry_after}')
        send_webhook(err_msg_list)
        time.sleep(retry_after)
        # Make the request again
        if retry_after < 5:
            res = make_request(method, path, retry_after+1, **kwargs)
        return res

def sync_ad_to_swit(
    ad_sync: dict,
    log_msg_list: list
):
    '''provision from AD to Swit'''
    # get swit users
    def _get_swit_users():
        page = 0
        swit_users = []
        while True:
            page += 1
            res = make_request('GET','/organization.user.list',
                params={
                    'cnt':1000,
                    'page':page,
                },timeout=10)
            new_users = res.json()['data']['users']
            if not new_users:
                break
            swit_users += new_users
        return swit_users
    def _get_users_mapped(swit_users):
        # email-swit_user_id mapping
        email_swit_id_dictionary = {user['email']:user['user_id'] for user in swit_users}
        # AD user DN - swit user ID mapping
        ad_swit_user_mapped = {
            user['distinguishedName']:{
                "swit_user_id": email_swit_id_dictionary[user['mail']],
                "idp_displayName": user['displayName'].split("/")[0],
                "idp_mobile": user['mobile']
            }
            for user in ad_sync['users'] \
                if user['distinguishedName'] and user['mail'] and user['mail'] in email_swit_id_dictionary}
        return ad_swit_user_mapped
    # Get teams
    def _get_swit_teams_by_ref():
        res = make_request('GET','/user.team.list',timeout=10)
        swit_teams = res.json()['data']['team']
        swit_teams_by_ref = {team['reference']:team for team in swit_teams if team['reference']}
        return swit_teams_by_ref, swit_teams[0]['team_id']

    def _get_ad_teams():
        # get AD teams
        ad_teams = [Team(
            distinguished_name=team['distinguishedName'],
            parent=team['memberOf'][0] if team['memberOf'] else '',
            members=team['member'],
            display_name=replace_special_characters(team['displayName'])
        ) \
        for team in ad_sync['teams'] \
            if team['distinguishedName'] and team['displayName'] \
                and team['distinguishedName'].startswith('CN=YOUR_ORG_NAME.') \
                and len([True for excluded_team_cn in TEAMS_TO_EXCLUDE if team['distinguishedName'].startswith(f'CN={excluded_team_cn},')])==0
            ]
        # Avoid duplicate display names
        existing_names = set()
        for team in ad_teams:
            name = team.display_name
            count = 2
            while name in existing_names:
                name = f"{team.display_name} ({count})"
                count += 1
            team.display_name = name
            existing_names.add(name)

        return ad_teams

    def _make_err_msg(res: requests.Response) -> str:
        return f"swit api error\nstatus_code : {res.status_code}\nerror message : {res.text}"

    swit_users = _get_swit_users()
    idp_swit_user_mapped = _get_users_mapped(swit_users)
    swit_teams_by_ref,root_team_id = _get_swit_teams_by_ref()
    ad_teams = _get_ad_teams()

    # Create or update teams
    print("팀 생성 로직 시작 ...")
    for team in ad_teams:
        if team.distinguished_name not in swit_teams_by_ref:
            # create
            log_msg_list.append(f"created team name : {team.display_name}")
            res = make_request('POST','/team.create',
                json={
                    'name':team.display_name,
                    'reference':team.distinguished_name,
                    'parent_id':root_team_id
                },
                timeout=10)
            if not res.ok:
                log_msg_list.append(_make_err_msg(res))
                send_webhook(log_msg_list)
                quit()
    print("팀 생성 로직 완료 ...")
    log_msg_list.append(f"team count : {len(ad_teams)}")
    # Configure team hierarchy
    print("팀 정보 동기화 로직 시작 ...")
    swit_teams_by_ref_updated,_ = _get_swit_teams_by_ref()
    for team in ad_teams:
        swit_team = swit_teams_by_ref_updated.get(team.distinguished_name)
        if not swit_team:
            continue
        ## check if team info is up-to-date
        parent_swit_team = swit_teams_by_ref_updated.get(team.parent, {"team_id":""})

        if team.display_name != swit_team['team_name'] or \
            parent_swit_team["team_id"] != swit_team['parent_id']:
            # update team info
            log_msg_list.append(f"updated team name : {swit_team['team_name']} -> {team.display_name}")
            res = make_request('POST','/team.update',
                json={
                    'id':swit_team['team_id'],
                    'reference':swit_team['reference'],
                    'name':team.display_name,
                    'parent_id':swit_teams_by_ref_updated[team.parent]['team_id'] if team.parent in swit_teams_by_ref_updated else root_team_id,
                },
                timeout=10)
            if not res.ok:
                log_msg_list.append(_make_err_msg(res))

        ## check if team members are up-to-date
        current_team_member_ids = set([idp_swit_user_mapped[member_dn]['swit_user_id'] for member_dn in team.members \
            if ',OU=Groups,' not in member_dn and member_dn in idp_swit_user_mapped])
        past_team_member_ids = set(swit_team['users'])
        # add members
        members_to_add = current_team_member_ids-past_team_member_ids
        if members_to_add:
            res = make_request('POST','/team.user.add',json={
                'id':swit_team['team_id'],
                'user_ids':list(members_to_add)
            },timeout=10)
            if not res.ok:
                log_msg_list.append(_make_err_msg(res))

        # remove members
        members_to_remove = past_team_member_ids-current_team_member_ids
        if members_to_remove:
            res = make_request('POST','/team.user.remove',json={
                'id':swit_team['team_id'],
                'user_ids':list(members_to_remove)
            },timeout=10)
            if not res.ok:
                log_msg_list.append(_make_err_msg(res))
    print("팀 정보 동기화 로직 종료 ...")
    # Remove unused teams
    print("팀 삭제 로직 시작 ...")
    prefix = '(removed) '
    ad_team_dns = [ad_team.distinguished_name for ad_team in ad_teams]
    for team_dn,swit_team in swit_teams_by_ref_updated.items():
        if team_dn in ad_team_dns:
            continue
        team_name = swit_team['team_name']
        if not team_name.startswith(prefix):
            team_name = prefix + team_name
        res = make_request('POST','/team.update',json={
            'id':swit_team['team_id'],
            'reference':team_dn,
            'name':team_name,
            'parent_id':root_team_id,
        },timeout=10)
        log_msg_list.append(f"removed team name : {team_name}")
        if not res.ok:
            log_msg_list.append(_make_err_msg(res))
    print("팀 삭제 로직 종료 ...")
    # 이름, 전화번호 채우기
    def _is_diff_name(swit_user, idp_user):
        return swit_user["user_name"] != idp_user['idp_displayName']

    # 변경할 전화번호인지 여부
    def _is_update_tel(swit_user_mapped, idp_user):
        if not idp_user.get('idp_mobile'):
            return False
        return swit_user_mapped[idp_user['swit_user_id']].get('tel', '') != idp_user['idp_mobile']

    swit_user_id_mapped = {
        swit_user['user_id']: swit_user
        for swit_user in swit_users
    }
    print("유저 정보 동기화 로직 시작 ...")
    updated_count = 0
    for idp_user in idp_swit_user_mapped.values():
        request_body = {}
        if _is_diff_name(swit_user_id_mapped[idp_user['swit_user_id']], idp_user) or _is_update_tel(swit_user_id_mapped, idp_user):
            request_body = {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "Operations": []
            }
            if _is_diff_name(swit_user_id_mapped[idp_user['swit_user_id']], idp_user):
                request_body['Operations'].append(
                    {
                        "op": "Replace",
                        "path": "displayName",
                        "value": idp_user['idp_displayName']
                    }
                )
            if _is_update_tel(swit_user_id_mapped, idp_user):
                request_body['Operations'].append(
                    {
                        "op": "Replace",
                        "path": "phoneNumbers[type eq \"mobile\"].value",
                        "value": idp_user['idp_mobile']
                    }
                )
            updated_count += 1
            if updated_count%5 == 0:
                print(f"update count : {updated_count}")
            make_request(
                "PATCH",
                f"/scim/v2/Users/{idp_user['swit_user_id']}",
                base_url="https://saml.swit.io",
                json=request_body,
                timeout=10
            )
    print("유저 정보 동기화 로직 종료 ...")
    # with open("mm.json","w",encoding="utf-8") as file:
    #     json.dump(print_text, file, ensure_ascii=False, indent=4)
    log_msg_list.append(f"총 idp 유저 수 : {len(idp_swit_user_mapped)}")
    log_msg_list.append(f"총 수정 유저 수 : {updated_count}")
    return "end"

def swit_user_update():
    print("idp 조직정보 가져오기 시작 ...")
    log_msg_list = []
    tls_config = Tls(validate=ssl.CERT_REQUIRED, version=ssl.PROTOCOL_TLSv1_2)
    server = Server(
        os.getenv("IDP_SERVER_DOMAIN"),
        port=int(os.getenv("IDP_SERVER_PORT")),
        tls=tls_config,
        get_info=ALL
    )
    conn = Connection(server,
        user=os.getenv("IDP_LDAP_USER"),
        password=os.getenv("IDP_LDAP_PASSWORD"),
        auto_bind=True,
        client_strategy=SYNC,
        authentication=SIMPLE
    )
    # OU정보 IDP -> HQ -> Employee, Partners, VIP // CloudPC용 OU VDI Computers
    ad_data = {}
    targets = [
        {
            'attributes': ['distinguishedName', 'member', 'memberOf', 'displayName'],
            'OUs': ['Groups'],
            'results': [],
            'label': 'teams'
        },
        {
            'attributes': ['distinguishedName', 'mail', 'displayName', 'mobile'],
            'OUs': ['Employee','Partners','VIP'],
            'results': [],
            'label': 'users'
        }
    ]
    for target in targets:
        for ou in target['OUs']:
            conn.search(
                search_base=f'OU={ou},OU=HQ,OU=YOUR_ORG_NAME,DC=xxxx,DC=co,DC=kr',
                search_filter='(objectclass=*)',
                attributes=target['attributes'] #ALL_ATTRIBUTES
            )
            results = [dict(entry['attributes']) for entry in conn.response]
            target['results'] += results

        ad_data[target['label']] = target['results']
    print("idp 조직정보 가져오기 종료 ...")
    # provisioning
    sync_ad_to_swit(ad_data, log_msg_list)
    print("동기화 완료")
    log_msg_list.append("동기화 완료")
    send_webhook(log_msg_list)
