# SKB LDAP Provisioning

- 이 프로젝트는 SKB LDAP에서 사용하는 LDAP 서버에 접속하여 사용자와 팀 정보를 가져와 Swit에 반영하는 기능을 제공합니다.
- 이 프로젝트는 [공개 리포](https://github.com/swit-developers/provisioning-example)를 fork하여 SKB LDAP에 맞게 수정한 코드입니다.
  - 해당 리포는 프로비저닝을 직접 구현하고자 하는 고객사들이 종종 있어서 예제 코드를 제공하고자 만들었습니다.
- 공개 리포와 비교했을 때 특히 다음 사항은 SKB에서 사용하지 않으므로 주석 처리했습니다.
  - 신규 유저 생성(이 부분은 SSO로 대체합니다)
  - 유저 활성/비활성
  - 팀 순서 정렬
- 동기화 batch가 구동되는 시점
  1. main.py를 실행했을 때
  2. 매일 UTC 20:00(한국시간 05:00)에 스케줄러가 실행될 때
- 또한 Flask 서버(포트 6000)를 구동하고 있으며 http 통신으로도 batch 구동이 가능하기는 하지만, SKB의 유즈케이스만 보면 사실 필요하지는 않습니다. 어차피 이 프로젝트가 구동되는 VM을 외부에서 http로 접근할 수 없기 때문입니다.
- 웹을 통한 OAuth도 불가능하므로 혹시 토큰을 다시 입력해야 한다면, VM으로 직접 들어와서 `service_accounts.db` 파일을 cli로 직접 수정해주세요(sqlite 기반).
- VM과 관련한 구체적인 사항은 SRE 팀에 문의해주세요.
- SKB 조직 내에서 정상 작동을 확인하려면 https://swit-tech.atlassian.net/wiki/spaces/URD/pages/2109145141/SKB+PC 참고

-------------------------------------------
아래는 원본 리포 README.md 내용

This repository contains a Flask application designed for provisioning user and team data from an Identity Provider (IdP) to a designated Swit organization.

This example is focused on using LDAP as the IdP, but you can easily adapt it to work with other IdPs by modifying the `src/services/idp_data.py` file.

## Environment Variables
```
IS_RUNNING_LOCALLY=True # Set to False when running on the server
SWIT_CLIENT_ID={YOUR_SWIT_CLIENT_ID}
SWIT_CLIENT_SECRET={YOUR_SWIT_CLIENT_SECRET}
OPERATION_AUTH_KEY=1234
SCHEDULE_TIME='00:00'

# New user's default settings
DEFAULT_USER_LANGUAGE=en

# Logger
SWIT_WEBHOOK_URL=https://hook.swit.io/chat/xxxxxxxx/xxxxxx

TEAMS_TO_EXCLUDE="Admin Division"

# LDAP (only for LDAP)
LDAP_SERVER_DOMAIN=
LDAP_SERVER_PORT=
LDAP_USER=
LDAP_PASSWORD=
LDAP_SEARCH_BASE="OU=HQ,OU=ABC,DC=example,DC=com"
LDAP_USER_OUS=Employees,Partners
LDAP_GROUP_OUS=Groups
```

## Repository Structure

The repository is organized into several directories and files, each serving a specific purpose in the application:

### Root Directory

- `main.py`: The entry point of the Flask application.
- `requirements.txt`: Lists all the Python dependencies required by the application.
- `mypy.ini`: Configuration file for mypy, a static type checker for Python.

### `src/` Directory

This is the main directory containing the source code of the application.

- `app.py`: Initializes and configures the Flask application.
- `routes.py`: Contains the route definitions of the application.

#### `src/core/`

Contains core functionalities of the application.

- `constants.py`: Defines constants used throughout the application, mostly environment variables.
- `logger.py`: Configures logging for tracking events and errors.

#### `src/database.py`

Handles database operations, in particular, managing the service account's token.

#### `src/services/`

Contains various services that implement the application's business logic.

- `provision_manager.py`: Manages the provisioning process to prevent concurrent executions.
- `data_sync.py`: Manages the synchronization of data between the IdP and Swit.
- `idp_data.py`: Handles importing data from the IdP.
- `swit_api_client.py`: Manages interactions with the Swit API.
- `swit_dtos.py`: Defines Swit object types.
- `swit_oauth.py`: Implements OAuth helpers for Swit API authentication.
- `scheduler.py`: Allows the application to execute tasks periodically.

### `tests/` Directory

Contains unit tests for the application.

- `test_provision.py`: Tests the provisioning functionality of the application.


## Swit API endpoints used:

We're using the following Swit API endpoints in order:
1. `GET /organization.user.list`: Fetch all existing Swit users.
2. `GET /user.team.list`: Fetch all existing Swit teams.
3. `POST /organization.user.create`: Create a new Swit user for each user in the IdP if they don't already exist.
4. `PATCH https://saml.swit.io/scim/v2/Users/{swit_user_id}`: Update the Swit user's name and telephone number with the latest information from the IdP.
   * We're preparing Swit's own REST API for this purpose, but it's not ready yet.
5. `POST /organization.user.deactivate`: Deactivate all users in Swit who aren't in the IdP.
   * If you want to hard-delete the user instead, you can use `POST /organization.user.remove` instead.
6. `POST /organization.user.activate`: Activate all users in Swit who are in the IdP.
7. `POST /team.delete`: If any Swit team does not exist in the IdP, the team is deleted.
8. `POST /team.create`: If any team exists in the IdP but not in Swit, create a new team in Swit.
9. `POST /team.update` (again): Update Swit team names and parents with the latest information from the IdP.
10. `POST /team.sort`: Sort all Swit teams according to the IdP. 
11. `POST /team.user.add`: Add all users in the IdP to their respective teams in Swit.
12. `POST /team.user.remove`: Remove all users from their respective teams in Swit if they aren't in the IdP.
13. `POST /team.user.primary.update` (optional): If users are in multiple teams, set their primary team to the team they're in the IdP.
