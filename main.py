from __future__ import print_function

# TTD:
# TODO: pull out / organize logging into a startup method.
# TODO: can created group title be passed around as part of group object rather than separately?
# TODO: does new API simplify things?
# TODO: better way to do instructorLog?

import argparse
import datetime
import logging
import sys
import os
import re

import arcrest
import dateutil.parser
import dateutil.tz
from arcrest.manageorg._community import Group  # @UnusedImport
from arcresthelper import common, orgtools, securityhandlerhelper
from bs4 import BeautifulSoup
from bs4.builder._htmlparser import HTMLParserTreeBuilder

import config

from CanvasAPI import CanvasAPI

# secrets really is used during (import to change sensitive properties).
import secrets  # @UnusedImport
import util

## TODO: centralize the logging setup.
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

# Adjustable level to use for all logging
#loggingLevel = logging.DEBUG
loggingLevel = logging.INFO

logger = None  # type: logging.Logger
logFormatter = None  # type: logging.Formatter
courseLogHandlers = dict()
courseLoggers = dict()

def getCanvasInstance():
    return CanvasAPI(config.Canvas.API_BASE_URL,
                     authZToken=config.Canvas.API_AUTHZ_TOKEN)


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
        arcGIS = securityhandlerhelper.securityhandlerhelper(securityinfo)
    except common.ArcRestHelperError:
        raise

    if arcGIS is not None and not arcGIS.valid:
        raise RuntimeError(str('ArcGIS connection invalid: ' + arcGIS.message))

    return arcGIS


def getCourseIDsWithOutcome(canvas, courseIDs, outcome):
    """Get Canvas courses that have assignments marked with outcome indicating there should be a corresponding ArgGIS group."""
    matchingCourseIDs = set()
    for courseID in courseIDs:
        courseOutcomeGroupLinks = \
            canvas.getCoursesOutcomeGroupLinksObjects(courseID)

        # Is it possible to short-circuit this using itertools?
        matchingCourseIDs.update(
            set(courseID for outcomeLink in courseOutcomeGroupLinks
                if outcomeLink.outcome.id == outcome.id)
        )

    return matchingCourseIDs


def getCourseAssignmentsWithOutcome(canvas, courseIDs, outcome):
    """Get specific assignments from Canvas courses.  Remove assignments that are expired or aren't marked to match up with ArgGIS group."""
    matchingCourseAssignments = []
    for courseID in courseIDs:
        courseAssignments = canvas.getCoursesAssignmentsObjects(courseID)

        for assignment in courseAssignments:
            expirationTimestamp = assignment.lock_at or assignment.due_at
            expirationTime = dateutil.parser.parse(expirationTimestamp) if expirationTimestamp else RUN_START_TIME
            if (expirationTime < RUN_START_TIME):
                logger.info('Skipping Assignment {} for Course {}, expired on: {}'
                            .format(assignment,
                                    courseID,
                                    assignment.lock_at if assignment.lock_at else assignment.due_at))
                continue
            if not assignment.rubric:
                logger.info('Skipping Assignment {} for Course {}, no rubrics'
                            .format(assignment,
                                    courseID))
                continue
            for rubric in assignment.rubric:
                if rubric.outcome_id == outcome.id:
                    matchingCourseAssignments.append(assignment)
                    break
    return matchingCourseAssignments


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
    community = arcGISAdmin.community
    groupIDs = community.getGroupIDs(groupNames=title)

    if len(groupIDs) > 0:
        return community.groups.group(groupId=groupIDs.pop())

    return None


def addCanvasUsersToGroup(course, instructorLog, group, courseUsers):
    """Add new users to the ArcGIS group.  """
    groupNameAndID = util.formatNameAndID(group)
    
    if len(courseUsers) == 0:
        logger.info('No new users to add to ArcGIS Group {}'.format(groupNameAndID))
        return

    logger.info('Adding Canvas Users to ArcGIS Group {}: {}'.format(groupNameAndID, courseUsers))
    # ArcGIS usernames are U-M uniqnames with the ArcGIS organization name appended.
    user="NULL"
    arcGISFormatUsers = formatUsersNamesForArcGIS(user, courseUsers)
    results = group.addUsersToGroups(users=','.join(arcGISFormatUsers))
    usersNotAdded = results.get('notAdded')
    """:type usersNotAdded: list"""
    usersCount = len(arcGISFormatUsers)
    usersCount -= len(usersNotAdded) if usersNotAdded else 0
    instructorLog += 'Number of users added to group: {}\n\n'.format(usersCount)
    if usersNotAdded:
        logger.warning('Warning: Some or all users not added to ArcGIS group {}: {}'.format(groupNameAndID, usersNotAdded))
        instructorLog += 'Users not in group (these users need ArcGIS accounts created for them):\n' + '\n'.join(map(lambda userNotAdded:'* ' + userNotAdded, usersNotAdded)) + '\n\n' + 'ArcGIS group ID number:\n{}\n\n'.format(group.id)
    instructorLog += '- - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n'
    courseLogger = getCourseLogger(course.id, course.name)
    courseLogger.info(instructorLog)


def getCurrentArcGISMembers(group, groupNameAndID):
    groupAllMembers = {}
    with util.CaptureStdoutLines() as output:
        try:
            groupAllMembers = group.groupUsers()
        except Exception as exception:
            logger.info('Exception while getting users for ArcGIS group "{}": {}'.format(groupNameAndID, exception))
    if output:
        logger.info('Unexpected output while getting users for ArcGIS group "{}": {}'.format(groupNameAndID, output))
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
    with util.CaptureStdoutLines() as output:
        try:
            results = group.removeUsersFromGroup(','.join(groupUsers))
        except Exception as exception:
            logger.info('Exception while removing users from ArcGIS group "{}": {}'.format(groupNameAndID, exception))
    if output:
        logger.info('Unexpected output while removing users from ArcGIS group "{}": {}'.format(groupNameAndID, output))
    usersNotRemoved = results.get('notRemoved')
    """:type usersNotRemoved: list"""
    if usersNotRemoved:
        logger.warning('Warning: Some or all users not removed from ArcGIS group {}: {}'.format(groupNameAndID, usersNotRemoved))
        
    return results


def removeExistingGroupMembers(groupTitle, group,instructorLog,groupUsers):
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
    logger.info('Creating ArcGIS group: "{}"'.format(groupTitle))
    instructorLog += 'Creating ArcGIS group: "{}"\n'.format(groupTitle)
    with util.CaptureStdoutLines() as output:
        try:
            arcGISOrgTools = orgtools.orgtools(arcGIS)
            group = arcGISOrgTools.createGroup(groupTitle, groupTags)
        except Exception as exception:
            logger.info('Exception while creating ArcGIS group "{}": {}'.format(groupTitle, exception))
    if output:
        logger.info('Unexpected output while creating ArcGIS group "{}": {}'.format(groupTitle, output))
    return group, instructorLog


# Get ArcGIS group with this title (if it exists)
def lookForExistingArcGISGroup(arcGIS, groupTitle):
    """Find an ArgGIS group with a matching title."""
    logger.info('Searching for existing ArcGIS group "{}"'.format(groupTitle))
    with util.CaptureStdoutLines() as output:
        try:
            arcGISAdmin = arcrest.manageorg.Administration(securityHandler=arcGIS.securityhandler)
            group = getArcGISGroupByTitle(arcGISAdmin, groupTitle)
        except Exception as exception:
            logger.exception('Exception while searching for ArcGIS group "{}": {}'.format(groupTitle, exception))
    if output:
        logger.info('Unexpected output while searching for ArcGIS group "{}": {}'.format(groupTitle, output))
    return group

# Take two lists and separate out those only in first list, those only in second list, and those in both.
# Uses to sets to do this so duplicate entries will become singular and list order will be arbitrary.
def listDifferences(leftList, rightList):
    """Take 2 lists and return 3 lists of entries: only in first, only in seconds, only in both lists.  Element order is not preserved. Duplicates will be compressed."""
    
    leftOnly = list(set(leftList) - set(rightList))
    rightOnly = list(set(rightList) - set(leftList))
    both = list(set(rightList) & set(leftList))
               
    return leftOnly, rightOnly, both

# Look at lists of users already in group and those currently in the course and return new lists
# of only the users that need to be added and need to be removed, so unchanged people remain untouched.

def minimizeUserChanges(groupUsers, courseUsers):
    """Compute minimal changes to ArgGIS group membership so that members who don't need to be changed aren't changed."""
    logger.debug('groupUsers input: {}'.format(groupUsers))
    logger.debug('courseUsers input: {}'.format(courseUsers))
    
    # Based on current Canvas and ArcGIS memberships find obsolete users in ArcGIS group, new users in course,
    # and members in both (hence unchanged).
    minGroupUsers, minCourseUsers, unchangedUsers = listDifferences(groupUsers,courseUsers)
    
    logger.info('changedArcGISGroupUsers: {} changedCanvasUsers: {} unchanged Users {}'.format(minGroupUsers,minCourseUsers,unchangedUsers))
  
    return minGroupUsers, minCourseUsers


def formatUsersNamesForArcGIS(user, userList):
    """Convert list of Canvas user name to the format used in ArcGIS."""
    userList = [user + '_' + config.ArcGIS.ORG_NAME for user in userList]
    return userList


def updateArcGISGroupForAssignment(arcGIS, courseUserDictionary, groupTags, assignment, course,instructorLog):
    """" Make sure there is a corresponding ArcGIS group for this Canvas course and assignment.  Sync up the ArcGIS members with the Canvas course members."""
    
    groupTitle = '%s_%s_%s_%s' % (course.name, course.id, assignment.name, assignment.id)
    group = None
    group = lookForExistingArcGISGroup(arcGIS, groupTitle)
    
    if group is None:
        group, instructorLog = createNewArcGISGroup(arcGIS, groupTags, groupTitle,instructorLog)
        
    if group is None:
        logger.info('Problem creating or updating ArcGIS group "{}": No errors, exceptions, or group object.'.format(groupTitle))
        instructorLog += 'Problem creating or updating ArcGIS group "{}"\n'.format(groupTitle)
        # TODO: return from here?
    else:
            
        groupNameAndID = util.formatNameAndID(group)

        groupUsers= getCurrentArcGISMembers(group, groupNameAndID)
        groupUsersTrimmed = [re.sub('_\S+$','',gu) for gu in groupUsers]
        
        logger.debug('All ArcGIS users currently in Group {}: ArcGIS Users: {}'.format(groupNameAndID, groupUsers))
                
        courseUsers = [user.login_id for user in courseUserDictionary[course.id] if user.login_id is not None]
        logger.debug('All Canvas users in course for Group {}: Canvas Users: {}'.format(groupNameAndID, courseUsers))
        
        # compute the exact sets of users to change.
        changedArcGISGroupUsers, changedCourseUsers = minimizeUserChanges(groupUsersTrimmed,courseUsers)
        
        # fix up the user name format for ArcGIS users names
        changedArcGISGroupUsers = formatUsersNamesForArcGIS(user, changedArcGISGroupUsers)       
        
        logger.info('Minimal list of users to remove from ArcGIS: Group {}: ArcGIS Users: {}'.format(groupNameAndID, changedArcGISGroupUsers))
        logger.info('Minimal list of user to add from Canvas course for ArcGIS: Group {}: Canvas Users: {}'.format(groupNameAndID, changedCourseUsers))
        
        # Now remove and add users from group
        instructorLog, results = removeExistingGroupMembers(groupTitle, group,instructorLog,changedArcGISGroupUsers)
        addCanvasUsersToGroup(course, instructorLog, group,changedCourseUsers)


# For all the assignments and their courses update the ArcGIS group.
def updateArcGISGroupsForAssignments(arcGIS, assignments, courseDictionary,courseUserDictionary):
    """For each assignment listed ensure there is an ArcGIS group corresponding to the Canvas course / assignmen."""
    global logger  # type: logging.Logger
    groupTags = ','.join(('kartograafr', 'umich'))

    for assignment in assignments:
        course = courseDictionary[assignment.course_id]
        instructorLog = ''
        updateArcGISGroupForAssignment(arcGIS, courseUserDictionary, groupTags, assignment, course,instructorLog)


def getCoursesByID(canvas, courseIDs):
    """Get Canvas course objects for the listed courses."""
    courses = {}
    for courseID in courseIDs:
        logger.info("getCoursesById: courseId: {}".format(courseID))
        courses[courseID] = canvas.getCourseObject(courseID)
    return courses


def getCoursesUsersByID(canvas, courseIDs, enrollmentType=None):
    """Get Canvas course members for specific course.  Can filter by members's Canvas role.

    :param canvas:
    :type canvas: CanvasAPI
    :param courseIDs:
    :type courseIDs: set or list
    :param enrollmentType: (optional) Canvas user enrollment type: 'student', 'teacher', etc.
    :type enrollmentType: str
    :return:
    """
    coursesUsers = {}
    for courseID in courseIDs:
        coursesUsers[courseID] = canvas.getCoursesUsersObjects(courseID, enrollmentType=enrollmentType,
                                                               params={'include[]': 'email'})
    return coursesUsers


def getCourseLogFilePath(courseID):
    """Each course will have a separate sub-log file.  This is the path to that file."""
    return os.path.realpath(os.path.normpath(os.path.join(
        config.Application.Logging.COURSE_DIRECTORY,
        courseID + config.Application.Logging.LOG_FILENAME_EXTENSION,
    )))


def getMainLogFilePath(nameSuffix=None):
    """Return the path/filename of the main log file."""
    mainLogName = config.Application.Logging.MAIN_LOG_BASENAME

    if nameSuffix is not None:
        mainLogName += '-' + str(nameSuffix)

    return os.path.realpath(os.path.normpath(os.path.join(
        config.Application.Logging.DIRECTORY,
        mainLogName + config.Application.Logging.LOG_FILENAME_EXTENSION,
    )))



def logToStdOut():
    """Have log output go to stdout in addition to any file."""
    root = logging.getLogger()
    root.setLevel(loggingLevel)
 
    ch = logging.StreamHandler(sys.stdout)
    #ch.setLevel(logging.DEBUG)
    ch.setLevel(loggingLevel)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

def getCourseLogger(courseID, courseName):
    """Set up course specific logger.
    
    :param courseID: ID number of the course
    :type courseID: str or int
    :param courseName: Name of the course
    :type courseName: str
    :return: A logging handler for a specific course's log file
    :rtype: logging.FileHandler
    """
    global courseLoggers  # type: dict
 
    courseID = str(courseID)

    if courseID in courseLoggers:
        return courseLoggers[courseID]

    logFormatterFriendly = logging.Formatter('Running at: %(asctime)s\n\n%(message)s', '%I:%M:%S %p on %B %d, %Y')

    logHandlerMain = logging.FileHandler(getMainLogFilePath())
    logHandlerMain.setFormatter(logFormatterFriendly)

    logHandlerCourse = logging.FileHandler(getCourseLogFilePath(courseID))
    logHandlerCourse.setFormatter(logFormatterFriendly)

    courseLogger = logging.getLogger(courseID)  # type: logging.Logger
    courseLogger.setLevel(loggingLevel)
    courseLogger.addHandler(logHandlerMain)
    courseLogger.addHandler(logHandlerCourse)

    courseLoggers[courseID] = courseLogger

    return courseLogger


def getCourseLogHandler(courseID, courseName):
    """Lookup the course specific logger for this course.
    
    :param courseID: ID number of the course
    :type courseID: str or int
    :param courseName: Name of the course
    :type courseName: str
    :return: A logging handler for a specific course's log file
    :rtype: logging.FileHandler
    """
    global logFormatter  # type: logging.Formatter
    global courseLogHandlers  # type: dict

    courseID = str(courseID)

    if courseID in courseLogHandlers:
        return courseLogHandlers[courseID]

    courseLogHandler = logging.FileHandler(getCourseLogFilePath(courseID))
    courseLogHandler.setFormatter(logFormatter)

    courseLogHandlers[courseID] = courseLogHandler

    return courseLogHandler


def closeAllCourseLoggerHandlers():
    global courseLoggers

    for (courseID, courseLogger) in courseLoggers.iteritems():  # type: logging.Logger
        for handler in courseLogger.handlers:  # type: logging.Handler
            handler.close()


def closeAllCourseLogHandlers():
    global courseLogHandlers

    for (courseID, courseLogHandler) in courseLogHandlers.iteritems():
        courseLogHandler.close()


def getCourseIDsFromConfigCoursePage(canvas, courseID, pageName):
    """Read hand edited list of Canvas course ids to process from a specific Canvas course page."""
    
    VALID_COURSE_URL_REGEX = '^https://umich\.instructure\.com/courses/[0-9]+$'
    pages = canvas.getCoursesPagesByNameObjects(courseID, 'course-ids')  # type: list of CanvasObject
    courseIDs = None

    if pages:
        configCoursePage = pages.pop()
        configCoursePageTree = BeautifulSoup(configCoursePage.body, builder=HTMLParserTreeBuilder())

        courseURLs = set(map(
            lambda a: a['href'],
            configCoursePageTree.find_all('a', href=re.compile(VALID_COURSE_URL_REGEX))))
        if courseURLs:
            courseIDs = map(lambda url: int(url.split('/').pop()), courseURLs)

    return courseIDs


def renameLogForCourseID(courseID=-1):
    """Change name of the course specific log file."""
    if courseID == -1:
        raise RuntimeError('Renaming logs requires either a course ID number to rename the log for that course, '
                           'or the None value to rename the main log.')

    if courseID is not None:
        courseID = str(courseID)
        oldLogName = getCourseLogFilePath(courseID)
        newLogName = getCourseLogFilePath(courseID + '-' + RUN_START_TIME_FORMATTED)
    else:
        oldLogName = getMainLogFilePath()
        newLogName = getMainLogFilePath(nameSuffix=RUN_START_TIME_FORMATTED)

    if os.path.isfile(oldLogName) is True:
        os.rename(oldLogName, newLogName)

    return (oldLogName, newLogName)


def emailLogForCourseID(courseID, recipients):
    """Email course information to a list of multiple recipients."""

    import smtplib
    from email.mime.text import MIMEText

    if not isinstance(recipients, list):
        recipients = [recipients]

    courseID = str(courseID)

    logContent = None

    # File may not exist if no changes were made to group.
    if os.path.isfile(getCourseLogFilePath(courseID)) is not True:
        logger.debug('No logfile {} for course: {}'.format(getCourseLogFilePath(courseID),courseID))
        return

    try:
        READ_BINARY_MODE = 'rb'
        logfile = open(getCourseLogFilePath(courseID), mode=READ_BINARY_MODE)
        logContent = logfile.read()
        logfile.close()
    except Exception as exception:
        logger.warning('Exception while trying to read logfile for course {courseID}: {exception}'
                       .format(**locals()))
        return
    
    message = MIMEText(logContent)
    message['From'] = config.Application.Email.SENDER_ADDRESS
    message['To'] = ', '.join(recipients)
    message['Subject'] = config.Application.Email.SUBJECT.format(**locals())
      
    if options.printEmail is True:
        logger.info("email message: {}".format(message))
    else:
        try:
            server = smtplib.SMTP(config.Application.Email.SMTP_SERVER)
            logger.debug("mail server: " + config.Application.Email.SMTP_SERVER)
            server.set_debuglevel(config.Application.Email.DEBUG_LEVEL)
            server.sendmail(config.Application.Email.SENDER_ADDRESS, recipients, message.as_string())
            server.quit()
            logger.info('Email sent to {recipients} for course {courseID}'.format(**locals()))
        except Exception as exception:
            logger.exception('Failed to send email to {recipients} for course {courseID}.  Exception: {exception}'
                         .format(**locals()))

    try:
        (oldLogName, newLogName) = renameLogForCourseID(courseID)
        logger.info('Renamed course log "{oldLogName}" to "{newLogName}"'.format(**locals()))
    except Exception as exception:
        logger.exception('Failed to rename log file for course {courseID}.  Exception: {exception}'
                         .format(**locals()))


def emailCourseLogs(courseInstructors):
    """ Loop through instructors to email course information to them.
    
    :param courseInstructors: Dictionary of courses to list of their instructors
    :type courseInstructors: dict
    """
    
    logger.info('Preparing to send email to instructors...')

    for courseID, instructors in courseInstructors.items():
        recipients = map(lambda instructor: instructor.sis_login_id +
                                            config.Application.Email.RECIPIENT_AT_DOMAIN,
                         instructors)
        emailLogForCourseID(courseID, recipients)


def main():
    """Setup and run Canvas / ArcGIS group sync.
    
    * parse command line arguments.
    * setup loggers.
    * connect to Canvas and  ArcGIS instances.
    * get list of relevant assignments from Canvas courses listed hand-edited Canvas page.
    * update membership of ArcGIS groups corresponding to Canvas course / assignments.
    """
    
    global logger
    global logFormatter
    global options

    logFormatter = util.Iso8601UTCTimeFormatter('%(asctime)s|%(levelname)s|%(name)s|%(message)s')

    logHandler = logging.FileHandler(getMainLogFilePath())
    logHandler.setFormatter(logFormatter)

    logger = logging.getLogger(config.Application.Logging.MAIN_LOGGER_NAME)  # type: logging.Logger
    logger.setLevel(loggingLevel)
    logger.addHandler(logHandler)
    
    # Add logging to stdout for OpenShift.
    logToStdOut()

    argumentParser = argparse.ArgumentParser()
    argumentParser.add_argument('--mail', '--email', dest='sendEmail',
                                action=argparse._StoreTrueAction,
                                help='email all available course logs to instructors, then rename all logs.')
    argumentParser.add_argument('--printMail', '--printEmail', dest='printEmail',
                                action=argparse._StoreTrueAction,
                                help='print emails to log instead of sending them.')
    options, unknownOptions = argumentParser.parse_known_args()

    logger.info('kart sys args: {} '.format(sys.argv[1:]))

    if unknownOptions:
        unknownOptionMessage = 'unrecognized arguments: %s' % ' '.join(unknownOptions)
        usageMessage = argumentParser.format_usage()

        logger.warning(unknownOptionMessage)
        logger.warning(usageMessage)

        # Also print usage error messages so they will appear in email to sysadmins, sent from crond
        print(unknownOptionMessage)
        print(usageMessage)

    logger.info('{} email to instructors with logs after courses are processed'
                .format('Sending' if options.sendEmail else 'Not sending'))

    canvas = getCanvasInstance()
    arcGIS = getArcGISConnection(config.ArcGIS.SECURITYINFO)

    outcomeID = config.Canvas.TARGET_OUTCOME_ID
    logger.info('Config -> Outcome ID to find: {}'.format(outcomeID))

    validOutcome = canvas.getOutcomeObject(outcomeID)

    if validOutcome is None:
        raise RuntimeError('Outcome ID {} was not found'.format(outcomeID))

    logger.info('Config -> Found valid Outcome: {}'.format(validOutcome))

    configCourseID = config.Canvas.CONFIG_COURSE_ID
    configCoursePageName = config.Canvas.CONFIG_COURSE_PAGE_NAME

    logger.info('Config -> Attempting to get course IDs from page '
                '"{configCoursePageName}" of course {configCourseID}...'
                .format(**locals()))

    courseIDs = getCourseIDsFromConfigCoursePage(canvas, configCourseID, configCoursePageName)

    if courseIDs is None:
        logger.warning('Warning: Config -> Course IDs not found in page '
                       '"{configCoursePageName}" of course {configCourseID}. '
                       'Using default course IDs instead.'
                       .format(**locals()))
        courseIDs = config.Canvas.COURSE_ID_SET
    else:
        logger.info('Config -> Found Course IDs in page '
                    '"{configCoursePageName}" of course {configCourseID}.'
                    .format(**locals()))

    logger.info('Config -> Course IDs to check for Outcome {}: {}'.format(validOutcome,
                                                                          list(courseIDs)))

    matchingCourseIDs = getCourseIDsWithOutcome(canvas, courseIDs,
                                                validOutcome)

    if len(matchingCourseIDs) == 0:
        raise RuntimeError('No Courses linked to Outcome {} were found'.format(validOutcome))

    logger.info('Config -> Found Course IDs for Outcome {}: {}'.format(validOutcome,
                                                                       list(matchingCourseIDs)))

    logger.info('Searching specified Courses for Assignments linked to Outcome {}'.format(validOutcome))
    matchingCourseAssignments = getCourseAssignmentsWithOutcome(
        canvas, matchingCourseIDs, validOutcome)

    if not matchingCourseAssignments:
        logger.info('No valid Assignments linked to Outcome {} were found'.format(validOutcome))
        return

    logger.info('Found Assignments linked to Outcome {}: {}'.format(validOutcome,
                                                                    ', '.join(map(str, matchingCourseAssignments))))

    courseDictionary = getCoursesByID(canvas, matchingCourseIDs)
    courseUserDictionary = getCoursesUsersByID(canvas, matchingCourseIDs)
    courseInstructorDictionary = getCoursesUsersByID(canvas, matchingCourseIDs, 'teacher')

    updateArcGISGroupsForAssignments(arcGIS, matchingCourseAssignments, courseDictionary, courseUserDictionary)

    closeAllCourseLoggerHandlers()

    if options.sendEmail:
        emailCourseLogs(courseInstructorDictionary)

    renameLogForCourseID(None)
    
    logger.info("current kartograaf run finished.")


if __name__ == '__main__':
    main()
