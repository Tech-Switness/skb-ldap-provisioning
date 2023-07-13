# Project Overview: Daily Provisioning System

This repository contains an exemplary provisioning system designed to update the user directory on a daily basis. Although the system is configured to use LDAP for Azure Directory as the Identity Provider (IdP) in this instance, it's flexible enough to be adapted to any system that can supply your organization's user directory.

Here's a brief description of the main components of the project:

* `main.py`: This is the primary script that the provisioning system runs. It orchestrates the different parts of the system.
* `src/api.py`: This file defines the API endpoints exposed by the provisioning system:
  * `/login`: Begin by visiting this endpoint to procure and store an admin access token.
  * `/user_update`: Make requests to this endpoint daily to refresh the user directory.
* `database`: This folder serves solely to store an admin access token, which holds the read and write privileges for the Swit User Directory.
* `service` folder comprises of:
  * `data_sync.py`: This is the core function that carries out the user directory updates.
  * `auth.py`: This is an authentication module responsible for making authenticated requests to Swit.
  * `scheduler.py`: It enables the main script to run daily, ensuring the user directory stays up-to-date.

### Environment variables example:

```
# Local settings and Database configuration
IS_RUNNING_LOCALLY = True
DB_HOST = 127.0.0.1
DB_PORT = 3306
DB_NAME = swit_sync_db
DB_USERNAME = root
DB_PASSWORD = securePassword123

# Swit application settings
CLIENT_ID = 7v9F9uvFXN35HH123Xx2
CLIENT_SECRET = 7s9kk3ZZZ372hh123PP7
APP_SECRET_KEY = A456B78C9D0E1F2G3H4I5J6K7L
OPERATION_AUTH_KEY = Z123Y456X789W012V3U4T5S6R

# Authentication with your IdP
# (Please add according to your Identity Provider's requirements)
# ...
```