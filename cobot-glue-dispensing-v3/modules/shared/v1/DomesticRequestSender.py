from modules.shared.v1.RequestSender import RequestSender
from modules.shared.v1.Request import Request


class DomesticRequestSender(RequestSender):
    def __init__(self, requestHandler):
        self.requestHandler = requestHandler

    def sendRequest(self, request: Request,data=None):

        if not isinstance(request, Request):
            return self.requestHandler.handleRequest(request,data)
        else:
            return self.requestHandler.handleRequest(request.to_dict())


    def handleBelt(self):
        self.requestHandler.handleBelt()

