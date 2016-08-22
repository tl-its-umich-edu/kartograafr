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

if '__main__' == __name__:
    main()
