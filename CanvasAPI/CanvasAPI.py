from RequestsPlus import *
from .models import CanvasObject


class CanvasAPI(RequestsPlus):
    class _QueryURIs(object):
        COURSES = '/courses/{courseID}'  #: Get a single Course by ID
        COURSES_OUTCOME_GROUP_LINKS = '/courses/{courseID}/outcome_group_links'
        SEARCH_ALL_COURSES = '/search/all_courses'
        OUTCOMES = '/outcomes/{outcomeID}'  #: Get a single Outcome by ID
        COURSES_ASSIGNMENTS = '/courses/{courseID}/assignments'
        COURSES_USERS = '/courses/{courseID}/users'

    def __init__(self, apiBaseURL, contentType=MIME_TYPE_JSON, authZToken=None, authZType=AUTHZ_TYPE_BEARER):
        """
        Set up CanvasAPI with the required authorization information

        :param apiBaseURL: Base URL for the Canvas API, usually "https://school.instructure.com/api/v1/"
        :type apiBaseURL: str
        :param contentType: MIME type value for "Content-Type" request header
        :type contentType: str
        :param authZToken: Token part of "Authorization" request header
        :type authZToken: str
        :param authZType: Type part of "Authotization" request header
        :type authZType: str
        :rtype: CanvasAPI
        """

        super(CanvasAPI, self).__init__(
            apiBaseURL, contentType=contentType, authZToken=authZToken, authZType=authZType
        )

    def jsonObjectHook(self, jsonObject):
        return CanvasObject(**jsonObject)

    def getOutcome(self, outcomeID):
        """
        Get Canvas Outcome object as requests Response object.  May be one of multiple pages.

        :param outcomeID: ID number of the Canvas outcome object to be retrieved
        :type outcomeID: int
        :return:
        :rtype: requests.models.Response
        """
        assert type(outcomeID) is int

        queryURI = self._QueryURIs.OUTCOMES.format(outcomeID=outcomeID)
        outcomeResponse = self.get(queryURI)

        return outcomeResponse

    def getOutcomeObject(self, outcomeID):
        """
        Get Canvas Outcome object as CanvasObject parsed from JSON

        :param outcomeID: ID number of the Canvas Outcome object to be retrieved
        :type outcomeID: int
        :return: An object representing the first Canvas Outcome contained
            in the API response, otherwise :class:`None<None>`
        :rtype: CanvasObject
        """
        assert type(outcomeID) is int

        outcomeObject = None
        outcomeResponse = self.getOutcome(outcomeID)
        if outcomeResponse.ok:
            outcomeObjects = self.responseCollection(outcomeResponse) \
                .jsonObjects(object_hook=self.jsonObjectHook)

            outcomeObjectCount = len(outcomeObjects)

            if outcomeObjectCount == 0:
                print 'log: successful response, but no outcome returned for ID: {}.' \
                    .format(outcomeID)
            else:
                if outcomeObjectCount > 1:
                    print 'log: successful response, but {} outcomes returned for ID: {}.' \
                        .format(outcomeObjectCount, outcomeID)

                outcomeObject = outcomeObjects.pop()

        return outcomeObject

    def getCoursesOutcomeGroupLinks(self, courseID):
        """
        Get Canvas Outcome Group objects as requests Response object.  May be one of multiple pages.

        :param courseID: ID number of the Canvas course object's Outcome Groups to be retrieved
        :type courseID: int
        :return:
        :rtype: requests.models.Response
        """
        assert type(courseID) is int

        queryURI = self._QueryURIs.COURSES_OUTCOME_GROUP_LINKS.format(courseID=courseID)
        response = self.get(queryURI)

        return response

    def getCoursesOutcomeGroupLinksObjects(self, courseID):
        """
        Get Canvas Outcome Group objects as CanvasObjects parsed from JSON

        :param courseID: ID number of the Canvas Course object to find Outcome Group objects
        :type courseID: int
        :return: An object representing the Canvas Outcome Groups contained
            in the API response, otherwise :class:`None<None>`
        :rtype: CanvasObject
        """
        assert type(courseID) is int

        courseOutcomeGroupLinks = None
        response = self.getCoursesOutcomeGroupLinks(courseID)
        if response.ok:
            courseOutcomeGroupLinks = self.responseCollection(response).collectAllResponsePages() \
                .jsonObjects(object_hook=self.jsonObjectHook)

        return courseOutcomeGroupLinks

    def getCoursesAssignments(self, courseID):
        """
        Get Canvas Assignments objects as requests Response object.  May be one of multiple pages.

        :param courseID: ID number of the Canvas course object's Assignment Objects to be retrieved
        :type courseID: int
        :return:
        :rtype: requests.models.Response
        """
        assert type(courseID) is int

        queryURI = self._QueryURIs.COURSES_ASSIGNMENTS.format(courseID=courseID)
        response = self.get(queryURI)

        return response

    def getCoursesAssignmentsObjects(self, courseID):
        """
        Get Canvas Assignment objects as CanvasObjects parsed from JSON

        :param courseID: ID number of the Canvas Course object to find Assignment objects
        :type courseID: int
        :return: An object representing the Canvas Assignments contained
            in the API response, otherwise :class:`None<None>`
        :rtype: CanvasObject
        """
        assert type(courseID) is int

        coursesAssignments = None
        response = self.getCoursesAssignments(courseID)
        if response.ok:
            coursesAssignments = self.responseCollection(response).collectAllResponsePages() \
                .jsonObjects(object_hook=self.jsonObjectHook)

        return coursesAssignments

    def getCoursesUsers(self, courseID):
        """
        Get Canvas Users objects as requests Response object.  May be one of multiple pages.

        :param courseID: ID number of the Canvas course object's User Objects to be retrieved
        :type courseID: int
        :return:
        :rtype: requests.models.Response
        """
        assert type(courseID) is int

        queryURI = self._QueryURIs.COURSES_USERS.format(courseID=courseID)
        response = self.get(queryURI)

        return response

    def getCoursesUsersObjects(self, courseID):
        """
        Get Canvas User objects as CanvasObjects parsed from JSON

        :param courseID: ID number of the Canvas Course object to find User objects
        :type courseID: int
        :return: An object representing the Canvas Users contained
            in the API response, otherwise :class:`None<None>`
        :rtype: CanvasObject
        """
        assert type(courseID) is int

        coursesUsers = None
        response = self.getCoursesUsers(courseID)
        if response.ok:
            coursesUsers = self.responseCollection(response).collectAllResponsePages() \
                .jsonObjects(object_hook=self.jsonObjectHook)

        return coursesUsers

    def getCourse(self, courseID):
        """
        Get Canvas Courses object as requests Response object.

        :param courseID: ID number of the Canvas course object to be retrieved
        :type courseID: int
        :return:
        :rtype: requests.models.Response
        """
        assert type(courseID) is int

        queryURI = self._QueryURIs.COURSES.format(courseID=courseID)
        response = self.get(queryURI)

        return response

    def getCourseObject(self, courseID):
        """
        Get Canvas Course object as CanvasObject parsed from JSON

        :param courseID: ID number of the Canvas Course object to find User objects
        :type courseID: int
        :return: An object representing the Canvas Users contained
            in the API response, otherwise :class:`None<None>`
        :rtype: CanvasObject
        """
        assert type(courseID) is int

        course = None
        response = self.getCourse(courseID)
        if response.ok:
            courseObjects = self.responseCollection(response) \
                .jsonObjects(object_hook=self.jsonObjectHook)

            courseCount = len(courseObjects)

            if courseCount == 0:
                print 'log: successful response, but no outcome returned for ID: {}.' \
                    .format(courseID)
            else:
                if courseCount > 1:
                    print 'log: successful response, but {} outcomes returned for ID: {}.' \
                        .format(courseCount, courseID)

                course = courseObjects.pop()

        return course

