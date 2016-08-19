import requests
import urlnorm

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

        :param response:
        :type response: requests.models.Response
        :return:
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
        If the URI (actually, just a partial URL, usually the path part) doesn't begin with
        the base URL for the API, concatenate the two into a new URL and return it.

        :param apiQueryURI: URI (actually, just a partial URL, usually the path part) for an API entry point.
        :type apiQueryURI: str
        :return:
        :rtype: str
        """
        assert isinstance(apiQueryURI, str)
        assert not util.stringContainsAllCharacters(apiQueryURI, '{}'), \
            'apiQueryURI contains unformatted arguments: "%s"' % apiQueryURI

        if apiQueryURI.startswith(self.apiBaseURL):
            return apiQueryURI
        else:
            return urlnorm.norm(self.apiBaseURL + '/' + apiQueryURI)

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

        print self.methodName() + '():', apiQueryURI, preparedAPIQueryURL

        try:
            response = sessionRequestMethod(preparedAPIQueryURL, **kwargs)
        except requests.exceptions.RequestException as e:
            print self._name + ' error: ' + e.message

        return response

    def errorString(self, response):
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
        print self.methodName() + '():', apiQueryURI

        return self._sendRequest(self.methodName(), apiQueryURI, **kwargs)

    def getAllResponsePages(self, response):
        return ResponseCollection(response, session=self.session).collectAllResponsePages()

    def post(self, apiQueryURI, params=None, **kwargs):
        return self._sendRequest(self.methodName(), apiQueryURI, params=params, **kwargs)
