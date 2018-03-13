## Configuration for OpenShift Production.

import os
import logging

class Application(object):
    class Email(object):
        DEBUG_LEVEL = False
        SMTP_SERVER = 'mail-relay.itd.umich.edu'
        SENDER_ADDRESS = '"ArcGIS-Canvas Service" <kartograafr-service@umich.edu>'
        RECIPIENT_AT_DOMAIN = '@umich.edu'
        SUBJECT = 'ArcGIS-Canvas logs for course ID {courseID}'

    class Logging(object):
        MAIN_LOGGER_NAME = 'kartograafr'
        DIRECTORY = '/var/log/kartograafr'
        COURSE_DIRECTORY = os.path.join(DIRECTORY, 'courses')
        MAIN_LOG_BASENAME = 'main'
        LOG_FILENAME_EXTENSION = '.log'
        DEFAULT_LOG_LEVEL = logging.INFO

class Canvas(object):
    API_BASE_URL = 'https://umich.instructure.com/api/v1/'

    API_AUTHZ_TOKEN = 'NEVEReverWILLyouKNOWmyNAME'

    ACCOUNT_ID = 1  # University of Michigan - Ann Arbor    ACCOUNT_ID = 306  # Test Account
    TARGET_OUTCOME_ID = 4353  # ArcGIS Group
    CONFIG_COURSE_ID = 214023  # kartograafr: Canvas/ArcGIS Integration
    
    # Name is found in page's URL.  Canvas changes "course_IDs" to "course-ids"
    CONFIG_COURSE_PAGE_NAME = 'course-ids'
    COURSE_ID_SET = set(( # Used iff IDs are not found in the configuration course page defined above
        85489,  # Practice Course for Lance Sloan (LANCE PRACTICE)
        114488,  # First ArcGIS Course (ARCGIS-1)
        135885,  # Another ArcGIS Course (ARCGIS-2)
    ))

class ArcGIS(object):
    ORG_NAME = 'umich' # For server URL (see below) and appended to ArcGIS usernames (i.e., "user_org")
    SECURITYINFO = {
        'security_type': 'Portal',  # Default: "Portal". "Required option" by bug in some ArcREST versions.
        'org_url': 'https://{}.maps.arcgis.com'.format(ORG_NAME),
        'username': '',
        'password': '',
    }
