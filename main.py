from __future__ import print_function

import datetime
import logging
import os
import re

import arcrest
import dateutil.parser
import dateutil.tz
from arcrest.manageorg._community import Group
from arcresthelper import common, orgtools, securityhandlerhelper
from bs4 import BeautifulSoup
from bs4.builder._htmlparser import HTMLParserTreeBuilder

import config
import util
from CanvasAPI import CanvasAPI

TIMEZONE_UTC = dateutil.tz.tzutc()
RUN_START_TIME = datetime.datetime.now(tz=TIMEZONE_UTC)

logger = None  # type: logging.Logger
logFormatter = None  # type: logging.Formatter
courseLogHandlers = dict()


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
    matchingCourseAssignments = []
    for courseID in courseIDs:
        courseAssignments = canvas.getCoursesAssignmentsObjects(courseID)

        for assignment in courseAssignments:
            expirationTimestamp = assignment.lock_at or assignment.due_at
            expirationTime = dateutil.parser.parse(expirationTimestamp) if expirationTimestamp else RUN_START_TIME
            if (expirationTime < RUN_START_TIME):
                logger.info('Skipping Assignment {}, expired on: {}'.format(assignment,
                                                                            assignment.lock_at if assignment.lock_at else assignment.due_at))
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


def createArcGISGroupsForAssignments(arcGIS, assignments, courseDictionary, courseUserDictionary):
    global logger  # type: logging.Logger
    groupTags = ','.join(('kartograafr', 'umich'))

    for assignment in assignments:
        course = courseDictionary[assignment.course_id]

        with util.LoggingContext(logger, handler=getCourseLogHandler(course.id, course.name)):
            groupTitle = '%s_%s_%s_%s' % (course.name, course.id, assignment.name, assignment.id)
            group = None

            logger.info('Searching for existing ArcGIS group "{}"'.format(groupTitle))

            with util.CaptureStdoutLines() as output:
                try:
                    arcGISAdmin = arcrest.manageorg.Administration(securityHandler=arcGIS.securityhandler)
                    group = getArcGISGroupByTitle(arcGISAdmin, groupTitle)
                except Exception as exception:
                    logger.exception('Exception while searching for ArcGIS group "{}": {}'.format(groupTitle, exception))

            if output:
                logger.info('Unexpected output while searching for ArcGIS group "{}": {}'
                            .format(groupTitle, output))

            if group is not None:
                groupNameAndID = util.formatNameAndID(group)
                logger.info('Found ArcGIS group: {}'.format(groupNameAndID))

                groupAllMembers = {}
                with util.CaptureStdoutLines() as output:
                    try:
                        groupAllMembers = group.groupUsers()
                    except Exception as exception:
                        logger.info(
                            'Exception while getting users for ArcGIS group "{}": {}'.format(groupNameAndID, exception))

                if output:
                    logger.info('Unexpected output while getting users for ArcGIS group "{}": {}'
                                .format(groupNameAndID, output))

                groupUsers = groupAllMembers.get('users')
                """:type groupUsers: list"""

                if not groupUsers:
                    logger.info('Existing ArcGIS group {} does not have users to remove.'.format(groupNameAndID))
                else:
                    logger.info('ArcGIS Users to be removed from ArcGIS Group {} '
                                'before reloading with all Canvas course users: {}'.format(groupNameAndID, groupUsers))

                    results = None
                    with util.CaptureStdoutLines() as output:
                        try:
                            results = group.removeUsersFromGroup(','.join(groupUsers))
                        except Exception as exception:
                            logger.info('Exception while removing users from ArcGIS group "{}": {}'
                                        .format(groupNameAndID, exception))

                    if output:
                        logger.info('Unexpected output while removing users from ArcGIS group "{}": {}'
                                    .format(groupNameAndID, output))

                    usersNotRemoved = results.get('notRemoved')
                    """:type usersNotRemoved: list"""

                    if usersNotRemoved:
                        logger.info('Warning: Some or all users not removed from ArcGIS group {}: {}'
                                    .format(groupNameAndID, usersNotRemoved))
            else:
                logger.info('Creating ArcGIS group: "{}"'.format(groupTitle))

                with util.CaptureStdoutLines() as output:
                    try:
                        arcGISOrgTools = orgtools.orgtools(arcGIS)
                        group = arcGISOrgTools.createGroup(groupTitle, groupTags)
                    except Exception as exception:
                        logger.info('Exception while creating ArcGIS group "{}": {}'.format(groupTitle, exception))

                if output:
                    logger.info('Unexpected output while creating ArcGIS group "{}": {}'
                                .format(groupTitle, output))

            if group is None:
                logger.info('Problem creating ArcGIS group "{}": No errors, exceptions, or group object.'
                            .format(groupTitle))
                continue

            groupNameAndID = util.formatNameAndID(group)

            courseUsers = [user.login_id for user in courseUserDictionary[course.id]]
            logger.info('Adding Canvas Users to ArcGIS Group {}: {}'.format(groupNameAndID, courseUsers))

            # ArcGIS usernames are U-M uniqnames with the ArcGIS organization name, separated by an underscore
            arcGISUsers = [user + '_' + config.ArcGIS.ORG_NAME for user in courseUsers]

            results = group.addUsersToGroups(users=','.join(arcGISUsers))

            usersNotAdded = results.get('notAdded')
            """:type usersNotAdded: list"""

            if usersNotAdded:
                logger.info('Warning: Some or all users not added to ArcGIS group {}: {}'
                            .format(groupNameAndID, usersNotAdded))


def getCoursesByID(canvas, courseIDs):
    courses = {}
    for courseID in courseIDs:
        courses[courseID] = canvas.getCourseObject(courseID)
    return courses


def getCoursesUsersByID(canvas, courseIDs, enrollmentType=None):
    """

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
    return os.path.realpath(os.path.normpath(os.path.join(
        config.Application.Logging.COURSE_DIRECTORY,
        courseID + '.log', )))


def getCourseLogHandler(courseID, courseName):
    """
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


def closeAllCourseLogHandlers():
    global courseLogHandlers

    for (courseID, courseLogHandler) in courseLogHandlers.iteritems():
        courseLogHandler.close()


def getCourseIDsFromConfigCoursePage(canvas, courseID, pageName):
    VALID_COURSE_URL_REGEX = '^https://umich\.instructure\.com/courses/[0-9]+$'
    pages = canvas.getCoursesPagesByNameObjects(138596, 'course-ids')  # type: list of CanvasObject
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


def main():
    global logger
    global logFormatter

    logFormatter = util.Iso8601UTCTimeFormatter('%(asctime)s|%(levelname)s|%(name)s|%(message)s')

    logHandler = logging.FileHandler(
        os.path.realpath(os.path.normpath(os.path.join(
            config.Application.Logging.DIRECTORY,
            config.Application.Logging.MAIN_LOG,
        ))))
    logHandler.setFormatter(logFormatter)

    logger = logging.getLogger('kartograafr')  # type: logging.Logger
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logHandler)

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
        logger.warning('Config -> Course IDs not found in page '
                       '"{configCoursePageName}" of course {configCourseID}. '
                       'Using default course IDs instead.'
                       .format(**locals()))
        courseIDs = config.Canvas.COURSE_ID_SET
    else:
        logger.warning('Config -> Found Course IDs in page '
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

    # if len(matchingCourseAssignments) == 0:
    if not matchingCourseAssignments:
        logger.info('No valid Assignments linked to Outcome {} were found'.format(validOutcome))
        return

    logger.info('Found Assignments linked to Outcome {}: {}'.format(validOutcome,
                                                                    ', '.join(map(str, matchingCourseAssignments))))

    courseDictionary = getCoursesByID(canvas, matchingCourseIDs)
    courseUserDictionary = getCoursesUsersByID(canvas, matchingCourseIDs)

    createArcGISGroupsForAssignments(arcGIS, matchingCourseAssignments, courseDictionary, courseUserDictionary)

    closeAllCourseLogHandlers()


if __name__ == '__main__':
    main()
