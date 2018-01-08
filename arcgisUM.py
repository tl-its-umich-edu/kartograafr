# Wrapper around calls to arcgis.  Helps with testing and future changes.

import datetime
import logging

logger = logging.getLogger(__name__)

from arcgis.gis import GIS

import dateutil.tz

import config

# secrets really is used during (import to change sensitive properties).
import secrets  # @UnusedImport

import util

##### Improved code tracebacks for exceptions
import traceback

def handleError(self, record):  # @UnusedVariable
    traceback.print_stack()
    
logging.Handler.handleError = handleError
#####

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
        arcGIS = GIS(securityinfo['org_url'],
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
    
    if len(gis_groups) > 0:
        return gis_groups.pop()

    return None


def addCanvasUsersToGroup(instructorLog, group, courseUsers):
    """Add new users to the ArcGIS group.  """
    groupNameAndID = util.formatNameAndID(group)
    
    logger.info("addCanvasUsersToGroup: enter")
    
    if len(courseUsers) == 0:
        logger.info('No new users to add to ArcGIS Group {}'.format(groupNameAndID))
        return instructorLog

    logger.info('Adding Canvas Users to ArcGIS Group {}: {}'.format(groupNameAndID, courseUsers))
    # ArcGIS usernames are U-M uniqnames with the ArcGIS organization name appended.
    user="NULL"
    arcGISFormatUsers = formatUsersNamesForArcGIS(user, courseUsers)
    logger.debug("addCanvasUsersToGroup: formatted: {}".format(arcGISFormatUsers))
    
    #results = group.addUsersToGroups(users=','.join(arcGISFormatUsers))
    results = group.add_users(arcGISFormatUsers)
    logger.debug("adding: results: {}".format(results))

    usersNotAdded = results.get('notAdded')
    """:type usersNotAdded: list"""
    usersCount = len(arcGISFormatUsers)
    usersCount -= len(usersNotAdded) if usersNotAdded else 0
    logger.debug("usersCount: {}".format(usersCount))
    logger.debug("aCUTG: instructorLog 1: [{}]".format(instructorLog))
    instructorLog += 'Number of users added to group: [{}]\n\n'.format(usersCount)
    logger.debug("aCUTG: instructorLog 2: [{}]".format(instructorLog))
    if usersNotAdded:
        logger.warning('Warning: Some or all users not added to ArcGIS group {}: {}'.format(groupNameAndID, usersNotAdded))
        instructorLog += 'Users not in group (these users need ArcGIS accounts created for them):\n' + '\n'.join(['* ' + userNotAdded for userNotAdded in usersNotAdded]) + '\n\n' + 'ArcGIS group ID number:\n{}\n\n'.format(group.id)
    instructorLog += '- - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n'
    logger.debug("aCUTG: instructorLog 3: [{}]".format(instructorLog))

    logger.info("addCanvasUsersToGroup: instructorLog: [{}]".format(instructorLog))
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

def removeListOfUsersFromArcGISGroup(group, groupNameAndID, groupUsers):
    """Remove only listed users from ArcGIS group."""

    if len(groupUsers) == 0:
        logger.info('No obsolete users to remove from ArcGIS Group {}'.format(groupNameAndID))
        return None

    logger.info('ArcGIS Users to be removed from ArcGIS Group [{}] [{}]'.format(groupNameAndID, ','.join(groupUsers)))
    results = None
    try:
            results = group.removeUsersFromGroup(','.join(groupUsers))
    except RuntimeError as exception:
            logger.error('Exception while removing users from ArcGIS group "{}": {}'.format(groupNameAndID, exception))
            
    usersNotRemoved = results.get('notRemoved')
    """:type usersNotRemoved: list"""
    if usersNotRemoved:
        logger.warning('Warning: Some or all users not removed from ArcGIS group {}: {}'.format(groupNameAndID, usersNotRemoved))
        
    return results


def removeSomeExistingGroupMembers(groupTitle, group,instructorLog,groupUsers):
    """Get list of ArgGIS users to remove from group and call method to remove them."""
    results = ''
    groupNameAndID = util.formatNameAndID(group)
    logger.info('Found ArcGIS group: {}'.format(groupNameAndID))
    instructorLog += 'Updating ArcGIS group: "{}"\n'.format(groupTitle)
    
    if not groupUsers:
        logger.info('Existing ArcGIS group {} does not have users to remove.'.format(groupNameAndID))
    else:
        results = removeListOfUsersFromArcGISGroup(group, groupNameAndID, groupUsers)
        
    return instructorLog, results

def createNewArcGISGroup(arcGIS, groupTags, groupTitle,instructorLog):
    """Create a new ArgGIS group.  Return group and any creation messages."""
   # group=None
    
    logger.info('Creating ArcGIS group: "{}"'.format(groupTitle))
    instructorLog += 'Creating ArcGIS group: "{}"\n'.format(groupTitle)
    try:
        group = arcGIS.groups.create(groupTitle,groupTags)
    except RuntimeError as exception:
        logger.info('Exception while creating ArcGIS group "{}": {}'.format(groupTitle, exception))
    
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

def formatUsersNamesForArcGIS(user, userList):
    """Convert list of Canvas user name to the format used in ArcGIS."""
    userList = [user + '_' + config.ArcGIS.ORG_NAME for user in userList]
    return userList
