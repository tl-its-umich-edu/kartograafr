from argparse import Namespace

import requests


class ResponseCollection(object):
    """
    The :class:`ResponseCollection<RequestsPlus.ResponseCollection>` object, a
    collection-like object to contain multiple
    :class:`Response<requests.models.Response>` objects.
    """

    class _LinksKeys(object):
        NEXT = 'next'
        CHILD_URL = 'url'

    def __init__(self, response=None, session=None):
        """
        :param response: A Response object
        :type response: requests.Response
        :param session: A Session object, helpful for reusing headers, etc.
        :type session: requests.Session
        """
        assert isinstance(response, requests.Response)
        self._currentResponse = response
        self._responses = [response]
        self._session = session if isinstance(session, requests.Session) \
            else requests.Session()

    def json(self, **kwargs):
        """

        :param kwargs:
        :return:
        :rtype: list of Any
        """
        allResponseJSON = []
        for (responseNumber, response) in enumerate(self._responses):
            responseJSON = response.json(**kwargs)
            if type(responseJSON) is not list:
                allResponseJSON.append(responseJSON)
            else:
                allResponseJSON.extend(responseJSON)

        return allResponseJSON

    def jsonObjects(self, **kwargs):
        """

        :param kwargs: Optional keyword arguments to pass along to `json()`
        :return: Namespace objects (not dictionaries) representing data from the JSON
        :rtype: list of Namespace
        """
        OBJECT_HOOK_KEY = 'object_hook'

        if OBJECT_HOOK_KEY not in kwargs:
            kwargs[OBJECT_HOOK_KEY] = lambda jsonObject: Namespace(**jsonObject)

        return self.json(**kwargs)

    def getNextPageURI(self, response=None):
        """
        :param response: The Response object queried for next page URI
        :type response: requests.models.Response
        :return: The URI from the "url" key of the Response object's "next" link, if one exists.  Otherwise, None.
        :rtype: str
        """
        response = response or self._currentResponse
        assert isinstance(response, requests.models.Response)

        return response.links.get(self._LinksKeys.NEXT, {}).get(self._LinksKeys.CHILD_URL)

    def getNextPageParams(self, response=None):
        """
        :param response: The Response object queried for next page params
        :type response: requests.models.Response
        :return: The URI params from the "url" key of the Response object's
            "next" link, if one exists.  Otherwise, None.
        :rtype: str
        """
        response = response or self._currentResponse
        assert isinstance(response, requests.models.Response)

        nextPageParams = None
        nextPageURI = self.getNextPageURI(response=response)
        if nextPageURI is not None:
            (_, nextPageParams) = nextPageURI.split('?')
        return nextPageParams

    def collectAllResponsePages(self):
        """
        :return: A ResponsePager object containing all pages following the initial Response
        :rtype: ResponseCollection
        """
        response = self._currentResponse
        """:type response: requests.models.Response"""

        while response.ok:
            nextPageParams = self.getNextPageParams(response)
            if nextPageParams is None:
                break
            nextPageRequest = response.request.copy()
            """:type nextPageRequest: requests.PreparedRequest"""
            nextPageRequest.prepare_url(nextPageRequest.url, nextPageParams)
            response = self._session.send(nextPageRequest)

            self._responses.append(response)
            self._currentResponse = response

        return self

    def getCurrentResponse(self):
        """
        :return: The current Response object
        :rtype: requests.models.Response
        """
        return self._currentResponse

    def getAllResponses(self):
        return self._responses

    def addResponse(self, response):
        assert isinstance(response, requests.models.Response)
        self._responses.append(response)

        return self
