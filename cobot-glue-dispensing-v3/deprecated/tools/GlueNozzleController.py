import traceback

from API.v1 import Constants
from API.Response import Response
from API.Request import Request
class GlueNozzleController:
    """
       Controller class to manage glue dispensing operations via the glue nozzle service.

       This class handles requests to start and stop glue dispensing, delegating the actual operations
       to the GlueNozzleService. It handles requests in the form of `Request` objects, which contain
       the necessary data and action types to control the glue nozzle.

       Attributes:
           glueNozzleService (GlueNozzleService): An instance of the GlueNozzleService class
               that performs the actual operations of starting and stopping the glue dispensing.
       """

    def __init__(self, glueNozzleService:'GlueNozzleService'):
        """
               Initializes the GlueNozzleController with a reference to the GlueNozzleService.

               Args:
                   glueNozzleService (GlueNozzleService): An instance of the GlueNozzleService class
                       responsible for handling glue dispensing operations.
               """

        self.glueNozzleService = glueNozzleService

    # def handleExecuteRequest(self,request:'Request'):
    #     """
    #             Handles incoming requests to either start or stop glue dispensing.
    #
    #             The method checks the action in the request, and based on whether it is an action to
    #             start or stop the glue dispensing, it delegates the operation to the `glueNozzleService`.
    #
    #             Args:
    #                 request (Request): A Request object containing the action and any necessary data
    #                     for the glue dispensing operation.
    #
    #             Returns:
    #                 dict: A response dictionary containing the status and message, returned as a Response object.
    #
    #             Raises:
    #                 Exception: If an error occurs while performing the glue dispensing operation, an exception is raised
    #                     and the traceback is printed.
    #             """
    #     # HANDLE GLUE ON
    #     if request.action == Constants.ACTION_START:
    #         try:
    #             self.glueNozzleService.sendCommand(request.data)
    #             return Response(Constants.RESPONSE_STATUS_SUCCESS, message="Glue turned on").to_dict()
    #         except Exception as e:
    #             traceback.print_exc()
    #             return Response(Constants.RESPONSE_STATUS_ERROR,
    #                             message=f"Error turning glue on: {e}").to_dict()
    #
    #     # HANDLE GLUE OFF
    #     elif request.action == Constants.ACTION_STOP:
    #         try:
    #             self.glueNozzleService.stopGlueDispensing()
    #             return Response(Constants.RESPONSE_STATUS_SUCCESS, message="Glue turned off").to_dict()
    #         except Exception as e:
    #             traceback.print_exc()
    #             return Response(Constants.RESPONSE_STATUS_ERROR,
    #                             message=f"Error turning glue off: {e}").to_dict()

