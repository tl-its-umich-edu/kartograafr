import os


class Application(object):
    class Email(object):
#        SMTP_SERVER = '127.0.0.1'
        SMTP_SERVER = 'docker.for.mac.localhost;1025'
        SENDER_ADDRESS = '"ArcGIS-Canvas Service Dev" <kartograafr-service-dev@umich.edu>'
        RECIPIENT_AT_DOMAIN = '@umich.edu'
        SUBJECT = 'ArcGIS-Canvas logs for course ID {courseID} (Dev)'


    # directory path for logging may depend on the platform.  /private/.... may be on osx
    # also '/tmp/log'
#     class Logging(object):
#         MAIN_LOGGER_NAME = 'kartograafr'
#         DIRECTORY = './tmp/log'
#         COURSE_DIRECTORY = os.path.join(DIRECTORY, 'courses')
#         MAIN_LOG_BASENAME = 'main'
#         LOG_FILENAME_EXTENSION = '.log'

        #        DIRECTORY = '/tmp/log'
        #        DIRECTORY = '/var/log/kartograafr'

    # directory path for logging may depend on the platform.  /private/.... may be on osx
    # also '/tmp/log'
    class Logging(object):
        MAIN_LOGGER_NAME = 'kartograafr'
        DIRECTORY = '/var/log/kartograafr'
        COURSE_DIRECTORY = os.path.join(DIRECTORY, 'courses')
        MAIN_LOG_BASENAME = 'main'
        LOG_FILENAME_EXTENSION = '.log'
 
        #        DIRECTORY = '/tmp/log'
        #        DIRECTORY = '/var/log/kartograafr'

class Canvas(object):
    API_BASE_URL = 'https://umich.instructure.com/api/v1/'

    API_AUTHZ_TOKEN = 'NEVEReverWILLyouKNOWmyNAME'

    ACCOUNT_ID = 306  # Test Account
    TARGET_OUTCOME_ID = 2501  # ArcGIS Mapping Skills
    CONFIG_COURSE_ID = 138596
    CONFIG_COURSE_PAGE_NAME = 'course-ids'
    COURSE_ID_SET = set(( # Used iff IDs are not found in the configuration course page defined above
        85489,  # Practice Course for Lance Sloan (LANCE PRACTICE)
        114488,  # First ArcGIS Course (ARCGIS-1)
        135885,  # Another ArcGIS Course (ARCGIS-2)
    ))


class ArcGIS(object):
    ORG_NAME = 'devumich' # For server URL (see below) and appended to ArcGIS usernames (i.e., "user_org")
    SECURITYINFO = {
        'security_type': 'Portal',  # Default: "Portal". "Required option" by bug in some ArcREST versions.
        'org_url': 'https://{}.maps.arcgis.com'.format(ORG_NAME),
        'username': '',
        'password': '',
    }
