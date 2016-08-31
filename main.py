from __future__ import print_function

import arcrest
from arcrest.manageorg._community import Group
from arcresthelper import common, orgtools, securityhandlerhelper

import config
from CanvasAPI import CanvasAPI
from util import CaptureStdoutLines


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
        raise TypeError('securityinfo type should be dict')

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
        courseAssignments = \
            canvas.getCoursesAssignmentsObjects(courseID)

        for assignment in courseAssignments:
            for rubric in assignment.rubric:
                if rubric.outcome_id == outcome.id:
                    matchingCourseAssignments.append(assignment)
                    break
    return matchingCourseAssignments


def getGroupByTitle(arcGISAdmin, title):
    """

    :param arcGISAdmin:
    :type arcGISAdmin: arcrest.manageorg.administration.Administration
    :param title:
    :type title: str
    :return: ArcGIS Group object with specified title or None
    :rtype: Group
    """
    community = arcGISAdmin.community
    groupIDs = community.getGroupIDs(groupNames=title)

    if len(groupIDs) > 0:
        return community.groups.group(groupId=groupIDs.pop())

    return None


def createGroupsForAssignments(arcGIS, assignments, courseDictionary, courseUserDictionary):
    groupTags = ','.join(('kartograafr', 'umich'))

    for assignment in assignments:
        course = courseDictionary[assignment.course_id]
        groupTitle = '%s_%s_%s_%s' % (course.name, course.id, assignment.name, assignment.id)
        group = None

        with CaptureStdoutLines() as output:
            try:
                arcGISAdmin = arcrest.manageorg.Administration(securityHandler=arcGIS.securityhandler)
                group = getGroupByTitle(arcGISAdmin, groupTitle)
            except Exception as exception:
                print('Exception searching for group "%s": ' % groupTitle, exception)

        if output.notEmpty:
            raise RuntimeError(output)

        if group is not None:
            print('Found group:', formatNameAndID(group))
        else:
            print('Creating group: "{}"'.format(groupTitle))

            with CaptureStdoutLines() as stdoutLines:
                try:
                    arcGISOrgTools = orgtools.orgtools(arcGIS)
                    group = arcGISOrgTools.createGroup(groupTitle, groupTags)
                except Exception as exception:
                    print('Exception creating group "{}": '.format(groupTitle), exception)

            if stdoutLines.notEmpty:
                raise RuntimeError(stdoutLines)

        if group is None:
            raise RuntimeError('Problem creating group "{}": '
                               'No errors, exceptions, or group object.'.format(groupTitle))

        groupUsers = group.addUsersToGroups(users=','.join(
            [user.login_id for user in courseUserDictionary[course.id]]
        ))

        if len(groupUsers['notAdded']) > 0:
            print('Users not added to group {}: {}'
                  .format(formatNameAndID(group), '"' + '", "'.join(groupUsers['notAdded']) + '"'))


def getCoursesByID(canvas, courseIDs):
    courses = {}
    for courseID in courseIDs:
        courses[courseID] = canvas.getCourseObject(courseID)
    return courses


def getCoursesUsersByID(canvas, courseIDs):
    coursesUsers = {}
    for courseID in courseIDs:
        coursesUsers[courseID] = canvas.getCoursesUsersObjects(courseID)
    return coursesUsers


def formatNameAndID(object):
    name = object.name if 'name' in object else object.title
    return '"{}" ({})'.format(name, object.id)


def formatNamesAndIDs(objects):
    return map(formatNameAndID, objects)


def main():
    canvas = getCanvasInstance()
    arcGIS = getArcGISConnection(config.ArcGIS.SECURITYINFO)

    outcomeID = config.Canvas.TARGET_OUTCOME_ID
    print('outcome ID to check:', outcomeID)

    validOutcome = canvas.getOutcomeObject(outcomeID)

    if validOutcome is None:
        raise RuntimeError('Outcome {} was not found'.format(outcomeID))

    # print('Found valid outcome: "{}" ({})'.format(validOutcome.title, validOutcome.id))
    print('Found valid outcome: ', formatNameAndID(validOutcome))

    courseIDs = config.Canvas.COURSE_ID_SET
    print('course IDs to check:', ', '.join(map(str, courseIDs)))

    matchingCourseIDs = getCourseIDsWithOutcome(canvas, courseIDs,
                                                validOutcome)

    if len(matchingCourseIDs) == 0:
        raise RuntimeError('No courses linked to Outcome ID {} were found'.format(outcomeID))

    print('matching course IDs:', ', '.join(map(str, matchingCourseIDs)))

    # TODO: Ignore assignments whose due/available dates have passed?
    matchingCourseAssignments = getCourseAssignmentsWithOutcome(
        canvas, matchingCourseIDs, validOutcome)

    if len(matchingCourseAssignments) == 0:
        raise RuntimeError('No course assignments linked to Outcome {} were found'.format(outcomeID))

    print('matching course assignments:', ', '.join(formatNamesAndIDs(matchingCourseAssignments)))

    courseDictionary = getCoursesByID(canvas, matchingCourseIDs)
    courseUserDictionary = getCoursesUsersByID(canvas, matchingCourseIDs)

    createGroupsForAssignments(arcGIS, matchingCourseAssignments, courseDictionary, courseUserDictionary)


if __name__ == '__main__':
    main()
