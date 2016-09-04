class Canvas(object):
    API_BASE_URL = 'https://umich.instructure.com/api/v1/'
    API_AUTHZ_TOKEN = ''  # Token goes here
    ACCOUNT_ID = 306  # Test Account
    TARGET_OUTCOME_ID = 2501  # ArcGIS Mapping Skills
    COURSE_ID_SET = {
        85489,  # Practice Course for Lance Sloan (LANCE PRACTICE)
        114488,  # First ArcGIS Course (ARCGIS-1)
        135885,  # Another ArcGIS Course (ARCGIS-2)
    }


class ArcGIS(object):
    ORG_NAME = 'devumich'
    SECURITYINFO = {
        'username': '',
        'password': '',
        'security_type': 'Portal',  # Default: "Portal". "Required option" by bug in some ArcREST versions.
        'org_url': 'https://{}.maps.arcgis.com'.format(ORG_NAME),
    }
