from __future__ import print_function

import datetime

import arcrest
import dateutil.parser
import dateutil.tz
from arcrest.manageorg._community import Group
from arcresthelper import common, orgtools, securityhandlerhelper

import config
import util
from CanvasAPI import CanvasAPI

runStartTime = datetime.datetime.now(tz=dateutil.tz.tzutc())


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
            {courseID for outcomeLink in courseOutcomeGroupLinks
             if outcomeLink.outcome.id == outcome.id}
        )

    return matchingCourseIDs


def getCourseAssignmentsWithOutcome(canvas, courseIDs, outcome):
    matchingCourseAssignments = []
    for courseID in courseIDs:
        courseAssignments = canvas.getCoursesAssignmentsObjects(courseID)

        for assignment in courseAssignments:
            expirationTimestamp = assignment.lock_at or assignment.due_at
            expirationTime = dateutil.parser.parse(expirationTimestamp) if expirationTimestamp else runStartTime
            if (expirationTime < runStartTime):
                print('Skipping Assignment {}, expired on:'.format(util.formatNameAndID(assignment)),
                      assignment.lock_at if assignment.lock_at else assignment.due_at)
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
    groupTags = ','.join(('kartograafr', 'umich'))

    for assignment in assignments:
        course = courseDictionary[assignment.course_id]
        groupTitle = '%s_%s_%s_%s' % (course.name, course.id, assignment.name, assignment.id)
        group = None

        print('Searching for existing ArcGIS group "{}"'.format(groupTitle))

        with util.CaptureStdoutLines() as output:
            try:
                arcGISAdmin = arcrest.manageorg.Administration(securityHandler=arcGIS.securityhandler)
                group = getArcGISGroupByTitle(arcGISAdmin, groupTitle)
            except Exception as exception:
                print('Exception while searching for ArcGIS group "{}":'.format(groupTitle), exception)

        if output:
            print('Unexpected output while searching for ArcGIS group "{}": {}'
                  .format(groupTitle, output))

        if group is not None:
            groupNameAndID = util.formatNameAndID(group)
            print('Found ArcGIS group:', groupNameAndID)

            groupAllMembers = {}
            with util.CaptureStdoutLines() as output:
                try:
                    groupAllMembers = group.groupUsers()
                except Exception as exception:
                    print('Exception while getting users for ArcGIS group "{}":'.format(groupNameAndID), exception)

            if output:
                print('Unexpected output while getting users for ArcGIS group "{}": {}'
                      .format(groupNameAndID, output))

            groupUsers = groupAllMembers.get('users')
            """:type groupUsers: list"""

            if not groupUsers:
                print('Existing ArcGIS group {} does not have users to remove.'.format(groupNameAndID))
            else:
                print('ArcGIS Users to be removed from ArcGIS Group {} '
                      'before reloading with all Canvas course users:'.format(groupNameAndID), groupUsers)

                results = None
                with util.CaptureStdoutLines() as output:
                    try:
                        results = group.removeUsersFromGroup(','.join(groupUsers))
                    except Exception as exception:
                        print('Exception while removing users from ArcGIS group "{}":'
                              .format(groupNameAndID), exception)

                if output:
                    print('Unexpected output while removing users from ArcGIS group "{}": {}'
                          .format(groupNameAndID, output))

                usersNotRemoved = results.get('notRemoved')
                """:type usersNotRemoved: list"""

                if usersNotRemoved:
                    print('Warning: Some or all users not removed from ArcGIS group {}:'
                          .format(groupNameAndID), usersNotRemoved)
        else:
            print('Creating ArcGIS group: "{}"'.format(groupTitle))

            with util.CaptureStdoutLines() as output:
                try:
                    arcGISOrgTools = orgtools.orgtools(arcGIS)
                    group = arcGISOrgTools.createGroup(groupTitle, groupTags)
                except Exception as exception:
                    print('Exception while creating ArcGIS group "{}":'.format(groupTitle), exception)

            if output:
                print('Unexpected output while creating ArcGIS group "{}": {}'
                      .format(groupTitle, output))

        if group is None:
            print('Problem creating ArcGIS group "{}": No errors, exceptions, or group object.'
                  .format(groupTitle))
            continue

        courseUsers = [user.login_id for user in courseUserDictionary[course.id]]
        print('Adding Canvas Users to ArcGIS Group {}:'.format(util.formatNameAndID(group)), courseUsers)

        # ArcGIS usernames are U-M uniqnames with the ArcGIS organization name, separated by an underscore
        arcGISUsers = [user + '_' + config.ArcGIS.ORG_NAME for user in courseUsers]

        results = group.addUsersToGroups(users=','.join(arcGISUsers))

        usersNotAdded = results.get('notAdded')
        """:type usersNotAdded: list"""

        if usersNotAdded:
            print('Warning: Some or all users not added to ArcGIS group {}:'
                  .format(util.formatNameAndID(group)), usersNotAdded)


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
    :param enrollmentType: Canvas user enrollment type: 'student', 'teacher', etc.
    :type enrollmentType: str
    :return:
    """
    coursesUsers = {}
    for courseID in courseIDs:
        coursesUsers[courseID] = canvas.getCoursesUsersObjects(courseID, enrollmentType=enrollmentType)
    return coursesUsers


def main():
    canvas = getCanvasInstance()
    arcGIS = getArcGISConnection(config.ArcGIS.SECURITYINFO)

    outcomeID = config.Canvas.TARGET_OUTCOME_ID
    print('Config -> Outcome ID to find:', outcomeID)

    validOutcome = canvas.getOutcomeObject(outcomeID)

    if validOutcome is None:
        raise RuntimeError('Outcome ID {} was not found'.format(outcomeID))

    validOutcomeName = util.formatNameAndID(validOutcome)
    print('Config -> Found valid Outcome:', validOutcomeName)

    courseIDs = config.Canvas.COURSE_ID_SET
    print('Config -> Course IDs to check for Outcome {}:'.format(validOutcomeName),
          list(courseIDs))

    matchingCourseIDs = getCourseIDsWithOutcome(canvas, courseIDs,
                                                validOutcome)

    if len(matchingCourseIDs) == 0:
        raise RuntimeError('No Courses linked to Outcome {} were found'.format(validOutcomeName))

    print('Config -> Found Course IDs for Outcome {}:'.format(validOutcomeName),
          list(matchingCourseIDs))

    print('Searching specified Courses for Assignments linked to Outcome', validOutcomeName)
    matchingCourseAssignments = getCourseAssignmentsWithOutcome(
        canvas, matchingCourseIDs, validOutcome)

    # if len(matchingCourseAssignments) == 0:
    if not matchingCourseAssignments:
        print('No valid Assignments linked to Outcome {} were found'.format(validOutcomeName))
        return

    print('Found Assignments linked to Outcome {}:'.format(validOutcomeName),
          ', '.join(util.formatNamesAndIDs(matchingCourseAssignments)))

    courseDictionary = getCoursesByID(canvas, matchingCourseIDs)
    courseUserDictionary = getCoursesUsersByID(canvas, matchingCourseIDs)

    createArcGISGroupsForAssignments(arcGIS, matchingCourseAssignments, courseDictionary, courseUserDictionary)


if __name__ == '__main__':
    main()
