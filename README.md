# Provisioning Example

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
