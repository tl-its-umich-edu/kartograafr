# Wrapper around calls to arcgis. Helps with testing and future changes.

import datetime
import json
import logging
import traceback
from io import StringIO
from operator import itemgetter

import arcgis
import dateutil.tz

import util
from configuration import config


# global variables and logging setup
def handleError(self, record):  # @UnusedVariable
    traceback.print_stack()


logger = logging.getLogger(__name__)
logging.Handler.handleError = handleError

TIMEZONE_UTC = dateutil.tz.tzutc()
RUN_START_TIME = datetime.datetime.now(tz=TIMEZONE_UTC)
RUN_START_TIME_FORMATTED = RUN_START_TIME.strftime('%Y%m%d%H%M%S')

MODIFY_MODES = {
    "add": {
        "verb": "add",
        "verbStem": "add",
        "verbPrep": "to",
        "methodName": "add_users"
    },
    "remove": {
        "verb": "remove",
        "verbStem": "remov",
        "verbPrep": "from",
        "methodName": "remove_users"
    }
}

# Hold parsed options
options = None

# TODO: required in this module?
courseLogHandlers = dict()
courseLoggers = dict()


def getArcGISConnection(securityinfo):
    """
    Get a connection object for ArcGIS based on configuration options
    
    :return: Connection object for the ArcGIS service
    :rtype: arcresthelper.orgtools.orgtools
    :raises: RuntimeError if ArcGIS connection is not valid
    :raises: arcresthelper.common.ArcRestHelperError for ArcREST-related errors
    """

    if not isinstance(securityinfo, dict):
        raise TypeError('Argument securityinfo type should be dict')

    try:
        arcGIS = arcgis.GIS(securityinfo['org_url'],
                     securityinfo['username'],
                     securityinfo['password']);
    except RuntimeError as exp:
        logger.error("RuntimeError: getArcGISConnection: {}".format(exp))
        raise RuntimeError(str('ArcGIS connection invalid: {}'.format(exp)))
    
    return arcGIS


def getArcGISGroupByTitle(arcGISAdmin, title):
    """
    Given a possible title of a group, search for it in ArcGIS
    and return a Group object if found or None otherwise.

    :param arcGISAdmin: ArcGIS Administration REST service connection object
    :type arcGISAdmin: arcrest.manageorg.administration.Administration
    :param title: Group title to be found
    :type title: str
    :return: ArcGIS Group object or None
    :rtype: Group or None
    """
    escapedTitle = title.translate(str.maketrans({ '"':  r'\"' }))
    searchString = f'title:"{escapedTitle}"'
    logger.debug("group search string: escaped: {}".format(searchString))
    
    try:
        gis_groups = arcGISAdmin.groups.search(searchString)
    except RuntimeError as exp:
        logger.error("arcGIS error finding group: {} exception: {}".format(searchString,exp))
        return None
    
    if len(gis_groups) > 0:
        return gis_groups.pop()

    return None


def modifyUsersInGroup(group: object, users: list, mode: str, instructorLog: str):
    """Depending on the mode, add or remove users from the given ArcGIS group"""

    logger.info("modifyUsersInGroup: enter")
    groupNameAndID = util.formatNameAndID(group)

    # Set mode-specific methods and variables
    if mode in MODIFY_MODES:
        modeDict = MODIFY_MODES[mode]
        verb, verbStem, verbPrep, methodName = itemgetter("verb", "verbStem", "verbPrep", "methodName")(modeDict)
        modifyUsersMethod = getattr(group, methodName)
        logger.debug(modifyUsersMethod)
    else:
        logger.error("Function was called with an invalid mode: " + mode)

    if len(users) == 0:
        logger.info(f"No users to {verb} {verbPrep} ArcGIS Group {groupNameAndID}")
        instructorLog += f"No users were {verbStem}ed.\n\n"
        logger.debug(f"modifyUsersInGroup: instructorLog: [\n{instructorLog}\n]")
        return instructorLog

    logger.info(f"{verbStem}ing Canvas Users {verbPrep} ArcGIS Group {groupNameAndID}: {users}")

    # Change Canvas usernames to the ArcGIS format
    # (ArcGIS usernames are U-M uniqnames with the ArcGIS organization name appended)
    arcGISFormatUsers = formatUsersNamesForArcGIS(users)
    logger.debug(f"modifyUsersInGroup: formatted: {arcGISFormatUsers}")

    listsOfFormattedUsernames = util.splitListIntoSublists(arcGISFormatUsers, 20)
    usersNotModified = []

    for listOfFormattedUsernames in listsOfFormattedUsernames:
        try:
            results = modifyUsersMethod(listOfFormattedUsernames)
            logger.debug(f"{verbStem}ing: results: {results}")
            usersNotModified += results.get(f"not{verbStem.capitalize()}ed")
        except RuntimeError as exception:
            logger.error(f"Exception while {verbStem}ing users {verbPrep} ArcGIS group '{groupNameAndID}': {exception}")
            return None

    usersModifiedCount = len(arcGISFormatUsers) - len(usersNotModified)
    logger.debug(f"usersModifiedCount: {usersModifiedCount}")
    instructorLog += f"Number of users {verbStem}ed {verbPrep} group: [{usersModifiedCount}]\n\n"
    if usersNotModified:
        notModifiedMessage = f"Some or all users not {verbStem}ed {verbPrep} ArcGIS group"
        if mode == "add":
            notModifiedMessage += " (These users likely need ArcGIS accounts set up)"
        logger.warning(
            f"Warning: {notModifiedMessage} {groupNameAndID} : {usersNotModified}"
        )
        instructorLog += f"{notModifiedMessage}:\n" + "\n".join(
            ["* " + userNotModified for userNotModified in usersNotModified]
        ) + "\n"

    logger.debug(f"modifyUsersInGroup: instructorLog: [\n{instructorLog}\n]")
    return instructorLog


def getCurrentArcGISMembers(group, groupNameAndID):
    groupAllMembers = {}

    try:
        groupAllMembers = group.get_members()
    except RuntimeError as exception:
        logger.error('Exception while getting users for ArcGIS group "{}": {}'.format(groupNameAndID, exception))
            
    groupUsers = groupAllMembers.get('users')
    """:type groupUsers: list"""
    return groupUsers


def createNewArcGISGroup(arcGIS, groupTags, groupTitle,instructorLog):
    """Create a new ArgGIS group.  Return group and any creation messages."""
    group=None
    
    logger.info('Creating ArcGIS group: "{}"'.format(groupTitle))
    instructorLog += 'Creating ArcGIS group: "{}"\n'.format(groupTitle)
    try:
        group = arcGIS.groups.create(groupTitle,groupTags)
    except RuntimeError as exception:
        logger.exception('Exception while creating ArcGIS group "{}": {}'.format(groupTitle, exception))
    
    return group, instructorLog


# Get ArcGIS group with this title (if it exists)
def lookForExistingArcGISGroup(arcGIS, groupTitle):
    """Find an ArgGIS group with a matching title."""
    logger.info('Searching for existing ArcGIS group "{}"'.format(groupTitle))
    try:
            group = getArcGISGroupByTitle(arcGIS, groupTitle)
    except RuntimeError as exception:
            logger.exception('Exception while searching for ArcGIS group "{}": {}'.format(groupTitle, exception))
            
    return group


def formatUsersNamesForArcGIS(userList):
    """Convert list of Canvas user name to the format used in ArcGIS."""
    userList = [user + '_' + config.ArcGIS.ORG_NAME for user in userList]
    return userList


def updateArcGISItem(item: arcgis.gis.Item, data: dict):
    itemType = arcgis.gis.Item
    assert isinstance(item, itemType), '"item" is not type "' + str(itemType) + '"'
    dataType = dict
    assert isinstance(data, dataType), '"data" is not type "' + str(dataType) + '"'

    with StringIO(json.dumps(data)) as dataJson:
        item.update(data = dataJson.read())