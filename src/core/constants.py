import os
import dotenv

dotenv.load_dotenv()

IS_RUNNING_LOCALLY = bool(os.environ.get('IS_RUNNING_LOCALLY'))
SWIT_CLIENT_ID = os.environ.get('SWIT_CLIENT_ID')
SWIT_CLIENT_SECRET = os.environ.get('SWIT_CLIENT_SECRET')
OPERATION_AUTH_KEY = os.environ.get('OPERATION_AUTH_KEY')

# In case of using a daily scheduler
SCHEDULE_TIME = os.environ.get('SCHEDULE_TIME')  # example: '20:00'. If you don't want to use scheduler, set None.

# New user's default settings
DEFAULT_USER_LANGUAGE = os.environ.get('DEFAULT_USER_LANGUAGE') or 'en'
DEFAULT_USER_TIMEZONE = os.environ.get('DEFAULT_USER_TIMEZONE') or 'Asia/Seoul'

# Logger
SWIT_WEBHOOK_URL = os.environ.get('SWIT_WEBHOOK_URL')

# In case of using CSV
IDP_USERS_CSV_FILE_PATH = os.environ.get('IDP_USERS_CSV_FILE_PATH')
IDP_TEAMS_CSV_FILE_PATH = os.environ.get('IDP_TEAMS_CSV_FILE_PATH')

# In case of using DB
DB_HOST = os.environ.get('DB_HOST') or 'localhost'
DB_PORT = int(os.environ.get('DB_PORT') or '3306')
DB_NAME = os.environ.get('DB_NAME')
DB_USERNAME = os.environ.get('DB_USERNAME')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

# For testing
SWIT_BASE_URL = os.environ.get('SWIT_BASE_URL') or 'https://openapi.swit.io'
