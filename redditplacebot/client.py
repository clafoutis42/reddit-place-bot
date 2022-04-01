import time
from typing import Dict, List, Optional

import requests.auth
from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .colors import Color
from .exceptions import HTTPError


class Client:
    DEFAULT_BACKOFF_FACTOR = 0.3

    AUTH_URL = "https://www.reddit.com/api/v1/access_token"
    QUERY_URL = "https://gql-realtime-2.reddit.com/query"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
        raise_errors: bool = False,
        retries: Optional[int] = None,
        backoff_factor: Optional[float] = None,
        session: Optional[Session] = None,
        headers: Optional[Dict] = None,
    ):
        """
        :param client_id: The client_id used to authenticate to the API.
        :param client_secret: The client_secret used to authenticate to the API.
        :param username: Authenticated user's reddit username.
        :param password: Authenticated user's reddit password.
        :param raise_errors: Whether the client should raise on HTTPErrors or not.
        :param retries: The max number of retries. None or 0 if disabled.
        :param backoff_factor: Backoff factor for the wait and retry algorithm.
                               Default: 0.3
        :param session: The session to use in the client.
                        When this is passed, `retries` and `backoff_factor` are ignored.
        :param headers: The default headers used for each requests.
        """
        self._client_id = client_id
        self._client_secret = client_secret
        self._username = username
        self._password = password

        self._raise_errors = raise_errors

        self._session = session
        self.__init_session(retries, backoff_factor or self.DEFAULT_BACKOFF_FACTOR)

        self.__token_info = None
        self.__headers = headers or {}
        self.__headers["User-Agent"] = f"{username}/0.1"

    def __init_session(self, retries: Optional[int], backoff_factor: float):
        """
        Initiates the session if it does not already exist.

        :param retries: The max number of retries. None or 0 if no retries.
        :param backoff_factor: Backoff factor for the wait and retry algorithm.
                               Default: 0.3
        """
        if self._session is not None:
            return
        self._session = Session()
        if retries:
            self.__init_retries(retries, backoff_factor)

    def __init_retries(self, retries: int, backoff_factor: float):
        """
        Initiates the retries with the given backoff factor.

        :param retries: The max number of retries.
        :param backoff_factor: Backoff factor for the wait and retry algorithm.
                               Default: 0.3
        """
        adapter = HTTPAdapter(
            max_retries=Retry(
                total=retries,
                read=retries,
                connect=retries,
                backoff_factor=backoff_factor,
            )
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    # #
    # # PROPERTIES
    # #

    @property
    def session(self) -> Session:
        return self._session

    @property
    def _is_valid_token(self) -> bool:
        """
        :return: Whether the token is valid or not (expired or non existing == invalid).
        """
        if self.__token_info is None:
            return False
        return (
            time.time() + 120
            < self.__token_info["created_at"] + self.__token_info["expires_in"]
        )

    @property
    def _token_info(self) -> Dict:
        """
        Token's infos are refreshed if it is expired.

        :return: The token's infos.
        """
        if not self._is_valid_token:
            self._refresh__token_info()
        return self.__token_info

    @property
    def _headers(self) -> Dict:
        """
        :return: The default headers.
        """
        token_type = self._token_info["token_type"]
        token = self._token_info["access_token"]
        return {"Authorization": f"{token_type} {token}", **self.__headers}

    # #
    # # PRIVATE METHODS
    # #

    def _refresh__token_info(self):
        """
        Get a new token and update the client's token information.

        :raise RefreshTokenError:
        """
        data = {
            "username": self._username,
            "password": self._password,
            "grant_type": "password",
        }

        auth = requests.auth.HTTPBasicAuth(self._client_id, self._client_secret)

        resp = self.session.post(self.AUTH_URL, auth=auth, data=data, headers=self.__headers)
        if HTTPError.related_exception(resp) is not None:
            raise HTTPError.related_exception(resp)
        self.__token_info = resp.json()
        self.__token_info["created_at"] = time.time()

    # #
    # # METHODS
    # #

    def _request(self, method: str, url: str, **kwargs) -> Response:
        """
        Make a prepared request with the client's credentials.

        :param method: The method used make the request.
        :param endpoint: The endpoint we want to make a request at.
        :param kwargs: The arguments to pass to `session.request`.
        :return: The request's response.
        """
        headers = kwargs.get("headers", dict())
        headers.update(self._headers)
        kwargs["headers"] = headers
        resp = self.session.request(method, url, **kwargs)
        if self._raise_errors and HTTPError.related_exception(resp) is not None:
            raise HTTPError.related_exception(resp)
        return resp

    def write_pixel(self, x: int, y: int, color: int):
        """

        :param x: The pixel's x axis.
        :param y: The pixel's y axis.
        :param color: The color's code.
        :return: Request's response.
        """
        data = {
            "operationName": "setPixel",
            "variables": {
                "input": {
                    "actionName": "r/replace:set_pixel",
                    "PixelMessageData": {
                        "coordinate": {"x": x, "y": y},
                        "colorIndex": color,
                        "canvasIndex": 0,
                    },
                }
            },
            "query": "mutation setPixel($input: ActInput!) {\n  act(input: $input) {\n    data {\n      ... on BasicMessage {\n        id\n        data {\n          ... on GetUserCooldownResponseMessageData {\n            nextAvailablePixelTimestamp\n            __typename\n          }\n          ... on SetPixelResponseMessageData {\n            timestamp\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n",  # noqa
        }

        return self._request("POST", self.QUERY_URL, json=data)
