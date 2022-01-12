# standard modules
import argparse, logging, os, re, smtplib, sys, traceback
from datetime import datetime
from email.message import EmailMessage

# third-party modules
from bs4 import BeautifulSoup
from bs4.builder._htmlparser import HTMLParserTreeBuilder
import dateutil.parser, dateutil.tz

# local modules
import arcgisUM
from CanvasAPI import CanvasAPI
from configuration import config
import util


# global variables and logging setup
def handleError(self, record):  # @UnusedVariable
    traceback.print_stack()


# Create log file directories (if necessary)
os.makedirs(config.Application.Logging.DIRECTORY + "/courses", exist_ok=True)

logging.Handler.handleError = handleError

# Adjustable level to use for all logging
logger = logging.getLogger(__name__)
loggingLevel = config.Application.Logging.DEFAULT_LOG_LEVEL
logger.error("loggingLevel: {}".format(loggingLevel))

logger = None  # type: logging.Logger
logFormatter = None  # type: logging.Formatter
courseLogHandlers = dict()
courseLoggers = dict()

TIMEZONE_UTC = dateutil.tz.tzutc()
RUN_START_TIME = datetime.now(tz=TIMEZONE_UTC)
RUN_START_TIME_FORMATTED = RUN_START_TIME.strftime('%Y%m%d%H%M%S')

# Hold parsed options
options = None


def getCanvasInstance():
    return CanvasAPI(config.Canvas.API_BASE_URL,
                     authZToken=config.Canvas.API_AUTHZ_TOKEN)


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


# Take two lists and separate out entries only in first list, those only in second list, and those in both.
# Uses sets to do this so duplicate entries will become singular and order in the list will be arbitrary.
def computeListDifferences(leftList, rightList):
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
    minGroupUsers, minCourseUsers, unchangedUsers = computeListDifferences(groupUsers,courseUsers)
    
    logger.info('changedArcGISGroupUsers: {} changedCanvasUsers: {} unchanged Users {}'.format(minGroupUsers,minCourseUsers,unchangedUsers))
  
    return minGroupUsers, minCourseUsers


def updateGroupUsers(courseUserDictionary, course, instructorLog, groupTitle, group):
    """Add remove / users from group to match Canvas course"""
    
    # get the arcgis group members and the canvas course members.
    groupNameAndID = util.formatNameAndID(group)
    groupUsers = arcgisUM.getCurrentArcGISMembers(group, groupNameAndID)
    logger.debug('group users: {}'.format(groupUsers))
    groupUsersTrimmed = [re.sub('_\S+$', '', gu) for gu in groupUsers]
    logger.debug('All ArcGIS users currently in Group {}: ArcGIS Users: {}'.format(groupNameAndID, groupUsers))
    canvasCourseUsers = [user.login_id for user in courseUserDictionary[course.id] if user.login_id is not None]
    logger.debug('All Canvas users in course for Group {}: Canvas Users: {}'.format(groupNameAndID, canvasCourseUsers))
    
    # Compute the exact sets of users to change.
    usersToRemove, usersToAdd = minimizeUserChanges(groupUsersTrimmed, canvasCourseUsers)

    logger.info('Users to remove from ArcGIS: Group {}: Users: {}'.format(groupNameAndID, usersToRemove))
    logger.info('Users to add to ArcGIS: Group {}: Users: {}'.format(groupNameAndID, usersToAdd))

    # Now update only the users in the group that have changed.
    instructorLog += f"Group: {groupNameAndID} \n\n"
    instructorLog = arcgisUM.modifyUsersInGroup(group, usersToRemove, "remove", instructorLog)
    instructorLog = arcgisUM.modifyUsersInGroup(group, usersToAdd, "add", instructorLog)
    instructorLog += "- - -\n"

    return instructorLog


def updateArcGISGroupForAssignment(arcGIS, courseUserDictionary, groupTags, assignment, course,instructorLog):
    """" Make sure there is a corresponding ArcGIS group for this Canvas course and assignment.  Sync up the ArcGIS members with the Canvas course members."""
     
    groupTitle = '%s_%s_%s_%s' % (course.name, course.id, assignment.name, assignment.id)
    
    group = arcgisUM.lookForExistingArcGISGroup(arcGIS, groupTitle)
     
    if group is None:
        group, instructorLog = arcgisUM.createNewArcGISGroup(arcGIS, groupTags, groupTitle,instructorLog)
    
    # if creation didn't work then log that.
    if group is None:
        logger.info('Problem creating or updating ArcGIS group "{}": Missing group object.'.format(groupTitle))
        instructorLog += 'Problem creating or updating ArcGIS group "{}"\n'.format(groupTitle)
    else: 
        # have a group.  Might be new or existing.
        instructorLog = updateGroupUsers(courseUserDictionary, course, instructorLog, groupTitle, group)
        
    courseLogger = getCourseLogger(course.id, course.name)
    logger.debug("update group instructor log: {}".format(instructorLog))
    courseLogger.info(instructorLog)


# For all the assignments and their courses update the ArcGIS group.
def updateArcGISGroupsForAssignments(arcGIS, assignments, courseDictionary,courseUserDictionary):
    """For each assignment listed ensure there is an ArcGIS group corresponding to the Canvas course / assignment."""

    groupTags = ','.join(('kartograafr', 'umich'))
    logger.debug("groupTags: {}".format(groupTags))
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

    for (courseID, courseLogger) in courseLoggers.items():  # type: logging.Logger
        for handler in courseLogger.handlers:  # type: logging.Handler
            handler.close()


def closeAllCourseLogHandlers():
    global courseLogHandlers

    for (courseID, courseLogHandler) in courseLogHandlers.items():
        courseLogHandler.close()


def getCourseIDsFromConfigCoursePage(canvas, courseID, config_course_page_name):
    """Read hand edited list of Canvas course ids to process from a specific Canvas course page."""

    regex_base = config.Canvas.BASE_URL.replace(".", "\\.")
    valid_course_url_regex = '^{}/courses/[0-9]+$'.format(regex_base)
    pages = canvas.getCoursesPagesByNameObjects(courseID, config_course_page_name)  # type: list of CanvasObject

    courseIDs = None
    if pages:
        configCoursePage = pages.pop()
        configCoursePageTree = BeautifulSoup(configCoursePage.body, builder=HTMLParserTreeBuilder())

        courseURLs = set(
            [a['href'] for a in configCoursePageTree.find_all('a', href=re.compile(valid_course_url_regex))]
        )
        if courseURLs:
            courseIDs = [int(url.split('/').pop()) for url in courseURLs]

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

    if not isinstance(recipients, list):
        recipients = [recipients]

    courseID = str(courseID)

    logContent = None

    # File may not exist if no changes were made to group.
    if os.path.isfile(getCourseLogFilePath(courseID)) is not True:
        logger.debug('No logfile {} for course: {}'.format(getCourseLogFilePath(courseID),courseID))
        return

    try:
        logfile = open(getCourseLogFilePath(courseID))
        logContent = logfile.read()
        logfile.close()
    except Exception as exception:
        logger.warning('Exception while trying to read logfile for course {courseID}: {exception}'
                       .format(**locals()))
        return

    message = EmailMessage()
    message['From'] = config.Application.Email.SENDER_ADDRESS
    message['To'] = ', '.join(recipients)
    message['Subject'] = config.Application.Email.SUBJECT.format(**locals())
    message.set_content(logContent)

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

    for courseID, instructors in list(courseInstructors.items()):
        recipients = [instructor.login_id + config.Application.Email.RECIPIENT_AT_DOMAIN for instructor in instructors]
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

    logger.info("Starting kartograafr")

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
    arcGIS = arcgisUM.getArcGISConnection(config.ArcGIS.SECURITY_INFO)

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
    
    logger.info("Finished current kartograafr run.")


if __name__ == '__main__':
    kartStartTime = datetime.now()
    try:
        main()
    except Exception as exp:
        logger.error("abnormal ending: {}".format(exp))
        traceback.print_exc(exp)
    finally:
        logger.info("Stopping kartograafr. Duration: {} seconds".format(datetime.now()-kartStartTime))