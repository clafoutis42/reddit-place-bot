from requests import Response

__all__ = [
    "HTTPAuthorizationError",
    "HTTPBadGatewayError",
    "HTTPBadRequestError",
    "HTTPConflictError",
    "HTTPError",
    "HTTPErrorDict",
    "HTTPForbiddenError",
    "HTTPGatewayTimeoutError",
    "HTTPNotFoundError",
    "HTTPNotImplementedError",
    "HTTPServerError",
    "HTTPServiceUnavailableError",
    "HTTPTooManyRequestError",
    "HTTPUnprocessableEntityError",
]


class HTTPError(Exception):
    """
    An exception containing the response of a request to be inspected.
    """

    def __init__(self, response: Response):
        super().__init__(f"{response.status_code}: {response.text}")
        self.response = response

    @classmethod
    def related_exception(cls, response: Response):
        """
        Gets the status code corresponding exception class and returns an exception
        of this type.

        :param response: The errored response.
        :return: The related exception.
        """
        if 200 <= response.status_code <= 299:
            return None
        error = HTTPErrorDict.get(response.status_code)
        if error is None:
            return cls(response)
        return error(response)


class HTTPBadRequestError(HTTPError):
    pass


class HTTPAuthorizationError(HTTPError):
    pass


class HTTPForbiddenError(HTTPError):
    pass


class HTTPNotFoundError(HTTPError):
    pass


class HTTPConflictError(HTTPError):
    pass


class HTTPUnprocessableEntityError(HTTPError):
    pass


class HTTPTooManyRequestError(HTTPError):
    pass


class HTTPServerError(HTTPError):
    pass


class HTTPNotImplementedError(HTTPError):
    pass


class HTTPBadGatewayError(HTTPError):
    pass


class HTTPServiceUnavailableError(HTTPError):
    pass


class HTTPGatewayTimeoutError(HTTPError):
    pass


HTTPErrorDict = {
    400: HTTPBadRequestError,
    401: HTTPAuthorizationError,
    403: HTTPForbiddenError,
    404: HTTPNotFoundError,
    409: HTTPConflictError,
    422: HTTPUnprocessableEntityError,
    429: HTTPTooManyRequestError,
    500: HTTPServerError,
    501: HTTPNotImplementedError,
    502: HTTPBadGatewayError,
    503: HTTPServiceUnavailableError,
    504: HTTPGatewayTimeoutError,
}
