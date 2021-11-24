from twisted.web.client import Agent
from twisted.internet import reactor
from twisted.internet.protocol import Protocol
from twisted.internet.defer import Deferred


class NotExpectedResponseCodeError(Exception):
    pass


class _BodyAgent(Protocol):
    def __init__(self, finished, response_code):
        self.response_code = response_code
        self.finished = finished
        self.body = ""

    def dataReceived(self, data):
        self.body += data

    def connectionLost(self, reason):
        self.finished.callback(self.body)


class CustomHttpAgent:
    """
    A class used to make request, retrieve response and return its body.

    Methods
    - get_response_body(request arguments)
      obtain request and return its body or raise NotExpectedResponseCodeError
      return Deffered
    """

    def __init__(self):
        self.reactor = reactor
        self.agent = Agent(self.reactor)

    def get_response_body(self, *args, **kwargs):
        response = self.agent.request("GET", *args, **kwargs)
        response.addCallback(self._check_status_code)
        response.addCallback(self._get_raw_body_data)
        return response

    @staticmethod
    def _get_raw_body_data(response):
        finished = Deferred()
        response.deliverBody(_BodyAgent(finished, response.code))
        return finished

    @staticmethod
    def _check_status_code(response):
        if response.code != 200:
            raise NotExpectedResponseCodeError(
                "Not Expected response code: {}, {}".format(response.code, response.phrase)
            )
        return response
