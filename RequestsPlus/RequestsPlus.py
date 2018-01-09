# The request types are now hard coded rather than obtained from variable.  

import requests
from url_normalize import url_normalize

import util
from .ResponseCollection import *

HTTP_HEADER_AUTHORIZATION = 'Authorization'
AUTHZ_TYPE_BEARER = 'Bearer'
MIME_TYPE_JSON = 'application/json'
HTTP_HEADER_CONTENT_TYPE = 'Content-type'


class RequestsPlus(util.UtilMixin, object):
    def __init__(self, apiBaseURL, contentType=MIME_TYPE_JSON, authZToken=None, authZType=AUTHZ_TYPE_BEARER):
        self._name = self.__class__.__name__
        self.apiBaseURL = apiBaseURL
        self.contentType = contentType
        self.authZToken = authZToken
        self.authZType = authZType
        self.session = requests.Session()
        self.session.headers.update(self._prepareHeaders())

    @staticmethod
    def responseCollection(response):
        """
        Convenience method to make a ResponseCollection
        object for a response.

        :param response: requests Response object, usually the first of multiple pages
        :type response: requests.models.Response
        :return: ResponseCollection object containing multiple response pages
        :rtype: ResponseCollection
        """
        return ResponseCollection(response)

    @property
    def _authZHeader(self):
        return {} if self.authZToken is None else \
            {HTTP_HEADER_AUTHORIZATION: ' '.join([self.authZType, self.authZToken + ''])}

    @property
    def _contentTypeHeader(self):
        return {} if self.contentType is None else \
            {HTTP_HEADER_CONTENT_TYPE: self.contentType}

    def _prepareHeaders(self):
        headers = {}
        headers.update(self._contentTypeHeader)
        headers.update(self._authZHeader)
        return headers

    def _prepareURL(self, apiQueryURI):
        """
        If the URI (actually just a partial URL, usually the path part) doesn't begin with
        the base URL for the API, concatenate the two into a new URL and return it.

        :param apiQueryURI: URI (actually, just a partial URL, usually the path part) for an API entry point.
        :type apiQueryURI: str
        :return: URL for the API query, ready for use
        :rtype: str
        """
        assert isinstance(apiQueryURI, str)
        assert not util.stringContainsAllCharacters(apiQueryURI, '{}'), \
            'apiQueryURI contains unformatted arguments: "%s"' % apiQueryURI

        if apiQueryURI.startswith(self.apiBaseURL):
            return apiQueryURI

        return url_normalize(self.apiBaseURL + '/' + apiQueryURI)

    def _sendRequest(self, httpMethod, apiQueryURI, **kwargs):
        """
        Append the specified query URI to the base URL,
        which is then sent to the REST API using the specified method.

        :param httpMethod: Name of the HTTP method used for the query
        :type httpMethod: str
        :param apiQueryURI: URI for the query, to be appended to the base URL
        :type apiQueryURI: str
        :return: Response object
        :rtype: requests.Response
        """
        preparedAPIQueryURL = self._prepareURL(apiQueryURI)
        response = None
        sessionRequestMethod = self.session.__getattribute__(httpMethod)

        try:
            response = sessionRequestMethod(preparedAPIQueryURL, **kwargs)
        except requests.exceptions.RequestException as e:
            print( self._name + ' error: ' + e) # Python 3 message doesn't exist anymore? 

        return response

    def errorString(self, response):
        """
        Return the HTTP status code and corresponding reason from a
        requests Response object.  If any errors.message strings exist,
        include them in the string.

        :param response: requests Response object containing the error
        :type response: requests.Response
        :return: Formatted errors
        :rtype: str
        """
        errorString = str(response.status_code) + ' - ' + response.reason
        try:
            errorString += '\nErrors:\n\t' + ',\n\t'.join(
                [error['message'] for error in response.json()['errors']]
            )
        except:
            pass

        return errorString

    def get(self, apiQueryURI, **kwargs):
        """
        Pass the request method and the specified query URI along for processing.

        :param apiQueryURI: URI for the query, to be appended to the base URL
        :type apiQueryURI: str
        :return: Response object
        :rtype: requests.Response
        """

        response = self._sendRequest("get", apiQueryURI, **kwargs)

        if not response.ok:
            raise RuntimeError('Error {response.status_code} "{response.reason}" for request: {apiQueryURI}'
                               .format(**locals()))

        return response

    def getAllResponsePages(self, response):
        """
        Convenience method to get a ResponseCollection which includes all pages
        of the API response.

        :param response:
        :return: ResponseCollection containing all response pages
        :rtype: RequestsPlus.ResponseCollection
        """
        return ResponseCollection(response, session=self.session).collectAllResponsePages()

    def post(self, apiQueryURI, params=None, **kwargs):
        """
        Pass the request method, the specified query URI, and parameters along for processing.

        :param apiQueryURI: URI for the query, to be appended to the base URL
        :type apiQueryURI: str
        :param params: Parameters to be sent along with the request
        :type params: mixed
        :return: Response object
        :rtype: requests.Response
        """

        return self._sendRequest("post", apiQueryURI, params=params, **kwargs)
