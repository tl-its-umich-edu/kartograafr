# Wrapper around calls to arcgis. Helps with testing and future changes.

# standard modules
import datetime, logging, json, traceback
from io import StringIO

# third-party modules
import arcgis, dateutil.tz

# local modules
from configuration import config
import util


# global variables and logging setup
def handleError(self, record):  # @UnusedVariable
    traceback.print_stack()


logger = logging.getLogger(__name__)
logging.Handler.handleError = handleError

TIMEZONE_UTC = dateutil.tz.tzutc()
RUN_START_TIME = datetime.datetime.now(tz=TIMEZONE_UTC)
RUN_START_TIME_FORMATTED = RUN_START_TIME.strftime('%Y%m%d%H%M%S')

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
    searchString = "title:"+title
    logger.debug("group search string: original: {}".format(searchString))

    # quote characters that are special in the group search.
    searchString = searchString.translate(str.maketrans({"?":  r"\?","*":  r"\*"}))

    logger.debug("group search string: escaped: {}".format(searchString))
    
    try:
        gis_groups = arcGISAdmin.groups.search(searchString)
    except RuntimeError as exp:
        logger.error("arcGIS error finding group: {} exception: {}".format(searchString,exp))
        return None
    
    if len(gis_groups) > 0:
        return gis_groups.pop()

    return None


def addCanvasUsersToGroup(group, courseUsers, instructorLog):
    """Add new users to a specific ArcGIS group"""

    logger.info("addCanvasUsersToGroup: enter")
    groupNameAndID = util.formatNameAndID(group)
    
    if len(courseUsers) == 0:
        logger.info('No new users to add to ArcGIS Group {}'.format(groupNameAndID))
        instructorLog += "No new users were added.\n\n"
        return instructorLog

    logger.info('Adding Canvas Users to ArcGIS Group {}: {}'.format(groupNameAndID, courseUsers))
    # ArcGIS usernames are U-M uniqnames with the ArcGIS organization name appended.
    arcGISFormatUsers = formatUsersNamesForArcGIS(courseUsers)
    logger.debug("addCanvasUsersToGroup: formatted: {}".format(arcGISFormatUsers))

    usersCount = len(arcGISFormatUsers)
    listsOfFormattedUsernames = util.splitListIntoSublists(arcGISFormatUsers, 20)
    usersNotAdded = []

    for listOfFormattedUsernames in listsOfFormattedUsernames:
        try:
            results = group.add_users(listOfFormattedUsernames)
            logger.debug("adding: results: {}".format(results))
            usersNotAdded += results.get('notAdded')
        except RuntimeError as exception:
            logger.error('Exception while removing users from ArcGIS group "{}": {}'.format(groupNameAndID, exception))
            return None

    usersCount -= len(usersNotAdded)
    logger.debug("usersCount: {}".format(usersCount))
    instructorLog += 'Number of users added to group: [{}]\n\n'.format(usersCount)
    if usersNotAdded:
        logger.warning('Warning: Some or all users not added to ArcGIS group {}: {}'.format(groupNameAndID, usersNotAdded))
        instructorLog += 'Users not in group (these users need ArcGIS accounts created for them):\n' + '\n'.join(
            ['* ' + userNotAdded for userNotAdded in usersNotAdded]
        ) + '\n'

    logger.debug("addCanvasUsersToGroup: instructorLog: [{}]".format(instructorLog))
    return instructorLog


def removeCanvasUsersFromGroup(group, groupUsers, instructorLog):
    """Remove a list of users from a specific Canvas group"""

    logger.info("removeCanvasUsersFromGroup: enter")
    groupNameAndID = util.formatNameAndID(group)

    if not groupUsers:
        logger.info('Existing ArcGIS group {} does not have users to remove.'.format(groupNameAndID))
        instructorLog += "No past users were removed.\n\n"
        return instructorLog

    logger.info('Removing past Canvas users from ArcGIS Group [{}] [{}]'.format(groupNameAndID, ','.join(groupUsers)))

    listsOfGroupUsers = util.splitListIntoSublists(groupUsers, 20)
    usersNotRemoved = []
    """:type usersNotRemoved: list"""

    for listOfGroupUsers in listsOfGroupUsers:
        try:
            results = group.remove_users(listOfGroupUsers)
            logger.debug("removing: results: {}".format(results))
            usersNotRemoved += results.get('notRemoved')
        except RuntimeError as exception:
            logger.error('Exception while removing users from ArcGIS group "{}": {}'.format(groupNameAndID, exception))
            return None

    usersRemovedCount = len(groupUsers) - len(usersNotRemoved)
    instructorLog += 'Number of users removed from group: [{}]\n\n'.format(usersRemovedCount)

    if usersNotRemoved:
        logger.warning('Warning: Some or all users not removed from ArcGIS group {}: {}'.format(groupNameAndID, usersNotRemoved))
        instructorLog += 'Users that could not be removed:\n' + '\n'.join(
            ['* ' + userNotRemoved for userNotRemoved in usersNotRemoved]
        ) + '\n'

    logger.debug("removeCanvasUsersFromGroup: instructorLog: [{}]".format(instructorLog))
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