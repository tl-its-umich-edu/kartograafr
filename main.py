import config
from CanvasAPI import *


def getCanvasInstance():
    return CanvasAPI(config.Canvas.API_BASE_URL, authZToken=config.Canvas.API_AUTHZ_TOKEN)


def getCourseIDsWithOutcome(canvas, courseIDs, outcome):
    matchingCourseIDs = set()
    for courseID in courseIDs:
        courseOutcomeGroupLinks = canvas.getCoursesOutcomeGroupLinksObjects(courseID)

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
            for rubric in assignment.rubric:
                if rubric.outcome_id == outcome.id:
                    matchingCourseAssignments.append(assignment)
                    break
    return matchingCourseAssignments


def main():
    canvas = getCanvasInstance()

    outcomeID = config.Canvas.TARGET_OUTCOME_ID
    verifiedOutcome = canvas.getOutcomeObject(outcomeID)

    assert verifiedOutcome is not None, \
        'Outcome {} was not found'.format(outcomeID)

    courseIDs = config.Canvas.COURSE_ID_SET
    print 'possible course IDs:', courseIDs

    matchingCourseIDs = getCourseIDsWithOutcome(canvas, courseIDs, verifiedOutcome)

    print 'matching course IDs:', matchingCourseIDs

    assert len(matchingCourseIDs) > 0, \
        'No courses linked to Outcome {} were found'.format(outcomeID)

    matchingCourseAssignments = getCourseAssignmentsWithOutcome(canvas, matchingCourseIDs, verifiedOutcome)

    print 'matching course assignments:', [
        (assignment.name, assignment.id)
        for assignment
        in matchingCourseAssignments]


if '__main__' == __name__:
    main()
