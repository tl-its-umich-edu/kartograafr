import config
from CanvasAPI import *


def getCanvasInstance():
    return CanvasAPI(config.Canvas.API_BASE_URL, authZToken=config.Canvas.API_AUTHZ_TOKEN)


def main():
    canvas = getCanvasInstance()

    outcomeID = config.Canvas.TARGET_OUTCOME_ID
    verifiedOutcome = canvas.getOutcomeObject(outcomeID)

    assert verifiedOutcome is not None, \
        'Outcome {} was not found'.format(outcomeID)

    matchingCourseIDs = set()  # Used for further processing

    print 'possible course IDs:', config.Canvas.COURSE_ID_SET

    for courseID in config.Canvas.COURSE_ID_SET:
        courseOutcomeGroupLinks = canvas.getCoursesOutcomeGroupLinksObjects(courseID)

        # Is it possible to short-circuit this using itertools?
        matchingCourseIDs.update(
            {courseID for outcomeLink in courseOutcomeGroupLinks
             if outcomeLink.outcome.id == verifiedOutcome.id}
        )

    print 'matching course IDs:', matchingCourseIDs

    assert len(matchingCourseIDs) > 0, \
        'No courses linked to Outcome {} were found'.format(outcomeID)

    matchingCourseAssignments = []

    for courseID in matchingCourseIDs:
        courseAssignments = canvas.getCoursesAssignmentsObjects(courseID)

        for assignment in courseAssignments:
            for rubric in assignment.rubric:
                if rubric.outcome_id == verifiedOutcome.id:
                    matchingCourseAssignments.append(assignment)
                    break

    print 'matching course assignments:', [
        (assignment.name, assignment.id)
        for assignment
        in matchingCourseAssignments]

    return

    if 1:
        """
        Get all pages of all courses, print the types of the data structures, the number of courses found,
        and the ID numbers of the first five courses.
        """
        coursesAllResponses = canvas.get(canvas.QUERY_URI_SEARCH_ALL_COURSES, responseClass=ResponseCollection)
        """:type coursesAllResponses: ResponseCollection"""
        coursesAllResponses.collectAllResponsePages()
        allCoursesJSON = coursesAllResponses.jsonObjects()

        print type(allCoursesJSON)
        print 'number of courses: {}'.format(len(allCoursesJSON))
        print type(allCoursesJSON[0])

        for aCourse in allCoursesJSON[0:5]:
            """:type aCourse: Namespace"""
            print aCourse.course.id

        print '- ' * 20

    return

    if 1:
        """
        Get the course data for the first course from our list of course IDs.
        Print the course ID from the data and its name.
        """
        testCourse = canvas.get(canvas.QUERY_URI_COURSES.format(courseID=COURSE_IDS[0]))
        testCourseJSON = testCourse.json(object_hook=lambda jsonObject: Namespace(**jsonObject))
        if testCourse.ok:
            print 'testCourse:', testCourseJSON.id, testCourseJSON.name
        else:
            print 'failed to get testCourse'
            print canvas.errorString(testCourse)

        print '- ' * 20

    if True:
        coursesFirstResponse = canvas.get(canvas.QUERY_URI_SEARCH_ALL_COURSES)
        print 'get courses:', len(coursesFirstResponse.json())

        print '- ' * 20

        coursesRequest = coursesFirstResponse.request
        """:type : requests.PreparedRequest"""

        print 'courses:', coursesFirstResponse
        print 'coursesRequest.url:', coursesRequest.url
        print 'coursesRequest.path_url:', coursesRequest.path_url
        print 'coursesRequest:', coursesRequest

        courseJSON = []
        while coursesFirstResponse:
            print 'page number of courses:', len(coursesFirstResponse.json())
            courseJSON += coursesFirstResponse.json()

            coursesPager = ResponseCollection(coursesFirstResponse)
            nextCourseQueryURI = coursesPager.getNextPageURI()

            if nextCourseQueryURI is None:
                break
            else:
                print nextCourseQueryURI
                coursesFirstResponse = canvas.get(nextCourseQueryURI)  # next URI already includes params

        print 'total number of courses:', len(courseJSON)


if '__main__' == __name__:
    main()
