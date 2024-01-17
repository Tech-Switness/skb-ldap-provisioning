import csv

from collections import Counter
from pydantic import BaseModel, Field, ConfigDict

from src.core.constants import IDP_USERS_CSV_FILE_PATH, IDP_TEAMS_CSV_FILE_PATH


class IdpUser(BaseModel):
    """A class to hold IdP user information"""
    model_config = ConfigDict(populate_by_name=True, strict=True, extra='ignore')

    ref_id: str = Field(..., alias='ref_id')
    name: str = Field(..., alias='name')
    email: str = Field(..., alias='email')
    phone_number: str = Field(..., alias='phone_number')

class IdpTeam(BaseModel):
    """A class to hold IdP team information"""
    model_config = ConfigDict(populate_by_name=True, strict=True, extra='ignore')

    ref_id: str = Field(..., alias='obj_id')
    name: str = Field(..., alias='name')
    parent_ref_id: str = Field(..., alias='parent_id')
    users: list[IdpUser] = Field(...)

def _data_from_csv(csv_file_path: str) -> list[dict[str, str]]:
    """Create a list to store the data"""
    with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
        return list(csv.DictReader(csv_file))

def import_idp_users() -> list[IdpUser]:
    """Import users from IdP"""
    file_path = IDP_USERS_CSV_FILE_PATH
    assert file_path is not None
    raw_idp_users = _data_from_csv(file_path)
    return [IdpUser(**raw_idp_user) for raw_idp_user in raw_idp_users]

def import_idp_teams(idp_users: list[IdpUser]) -> list[IdpTeam]:
    """Import teams from IdP"""
    file_path = IDP_TEAMS_CSV_FILE_PATH
    assert file_path is not None
    idp_users_by_ref_id = {idp_user.ref_id: idp_user for idp_user in idp_users}
    raw_idp_teams = _data_from_csv(file_path)
    idp_teams = []
    for raw_idp_team in raw_idp_teams:
        users = [idp_users_by_ref_id[ref_id] for ref_id in raw_idp_team['user_ref_ids'].split(',')
                 if ref_id in idp_users_by_ref_id]
        idp_team = IdpTeam(users=users, **raw_idp_team)
        idp_teams.append(idp_team)

    # ATTENTION: Assert that all ref_ids are unique
    ref_ids = [team.ref_id for team in idp_teams]
    counter = Counter(ref_ids)
    duplicates = [ref_id for ref_id, count in counter.items() if count > 1]
    assert not duplicates, f'Duplicated ref_id(s) from the IdP: {duplicates}'

    return idp_teams


# TODO: Implement this ldap function
"""
def _data_from_ldap():
    tls_config = Tls(validate=ssl.CERT_REQUIRED, version=ssl.PROTOCOL_TLSv1_2)
    server = Server(
        os.environ.get("IDP_SERVER_DOMAIN"),
        port=int(os.environ.get("IDP_SERVER_PORT")),
        tls=tls_config,
        get_info=ALL
    )
    conn = Connection(server,
        user=os.environ.get("IDP_LDAP_USER"),
        password=os.environ.get("IDP_LDAP_PASSWORD"),
        auto_bind=True,
        client_strategy=SYNC,
        authentication=SIMPLE
    )
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

"""