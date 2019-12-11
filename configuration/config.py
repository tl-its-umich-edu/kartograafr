import json, os

try:
    with open(os.getenv("ENV_FILE", "configuration/secrets/env.json")) as env_file:
        ENV = json.load(env_file)
except FileNotFoundError as fnfe:
    print("Default config file was not found. This is normal for the build; it should be provided for operation.")


class Application(object):
    class Email(object):
        DEBUG_LEVEL = False
        SMTP_SERVER = ENV.get("SMTP Server", "localhost:1025")
        SENDER_ADDRESS = ENV.get(
            "Email Sender Address", '"ArcGIS-Canvas Service Dev" <kartograafr-service-dev@umich.edu>'
        )
        RECIPIENT_AT_DOMAIN = "@umich.edu"
        SUBJECT = 'ArcGIS-Canvas logs for course ID {courseID} (Dev)'

    # Directory path for logging may depend on the platform. This setup is for Docker.
    class Logging(object):
        MAIN_LOGGER_NAME = 'kartograafr'
        DIRECTORY = ENV.get("Logging Directory", "/tmp/log/kartograafr")
        COURSE_DIRECTORY = os.path.join(DIRECTORY, 'courses')
        MAIN_LOG_BASENAME = 'main'
        LOG_FILENAME_EXTENSION = '.log'
        DEFAULT_LOG_LEVEL = ENV.get("Logging Level", "INFO")


class Canvas(object):
    BASE_URL = ENV.get("Canvas Base URL", "https://umich.test.instructure.com")
    API_BASE_URL = BASE_URL + '/api/v1/'
    API_AUTHZ_TOKEN = ENV.get("Canvas API Token", "")
    ACCOUNT_ID = ENV.get("Canvas Account ID", 306)  # Default is UM Canvas Test Account
    TARGET_OUTCOME_ID = 4353  # Canvas Outcome created for Kartograafr
    CONFIG_COURSE_ID = ENV.get("Canvas Config Course ID", 366944)
    CONFIG_COURSE_PAGE_NAME = 'course-ids'  # Not case-sensitive
    COURSE_ID_SET = set((
        # Used if IDs are not found in the configuration course page defined above
        366945,  # Practice Course for Sam Sciolla (Kartograafr Test Course)
    ))


class ArcGIS(object):
    # ORG_NAME for server URL (see below) and appended to ArcGIS usernames (i.e., "user_org")
    ORG_NAME = ENV.get("ArcGIS Org Name", "devumich")
    SECURITY_INFO = {
        'security_type': 'Portal',  # Default: "Portal"; "Required option" by bug in some ArcREST versions
        'org_url': 'https://{}.maps.arcgis.com'.format(ORG_NAME),
        'username': ENV.get("ArcGIS Username", ""),
        'password': ENV.get("ArcGIS Password", "")
    }