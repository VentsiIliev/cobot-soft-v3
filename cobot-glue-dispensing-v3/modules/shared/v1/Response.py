import json

class Response:
    def __init__(self, status: str, message: str = None, data: dict = None, error: dict = None):
        """
        Initializes a Response object.

        :param status: The status of the response, e.g., 'success' or 'failure'.
        :param message: A message describing the result of the request.
        :param data: The data returned with the response (optional).
        :param error: The error information, if any (optional).
        """
        self.status = status  # 'success' or 'failure'
        self.message = message if message is not None else {}  # Description of the result
        self.data = data if data is not None else {}  # Data returned with the response (optional)
        self.error = error if error is not None else {}  # Error information (optional)
    def to_dict(self) -> dict:
        """
        Convert the Response object to a dictionary for easy serialization (e.g., JSON).

        :return: Dictionary representation of the Response.
        """
        return {
            "status": self.status,
            "message": self.message,
            "data": self.data,
            "error": self.error
        }

    def to_json(self) -> str:
        """
        Convert the Response object to a JSON string.

        :return: JSON string representation of the Response.
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, response_dict: dict):
        """
        Create a Response object from a dictionary.

        :param response_dict: The dictionary representation of the response.
        :return: A Response object.
        """
        return cls(
            status=response_dict.get("status"),
            message=response_dict.get("message"),
            data=response_dict.get("data"),
            error=response_dict.get("error")
        )

    @classmethod
    def from_json(cls, response_json: str):
        """
        Create a Response object from a JSON string.

        :param response_json: The JSON string representation of the response.
        :return: A Response object.
        """
        response_dict = json.loads(response_json)
        return cls.from_dict(response_dict)

    def __repr__(self):
        """
        Return a string representation of the Response object.
        """
        return f"Response(status='{self.status}', message='{self.message}', data={self.data}, error={self.error})"


# Example Usage:

# # Creating a successful response (GET or POST request was successful)
# success_response = Response(status="success", message="Request processed successfully", data={"key": "value"})
# print(success_response)  # Output: Response(status='success', message='Request processed successfully', data={'key': 'value'}, error={})
#
# # Creating a failure response (POST request encountered an error)
# error_response = Response(status="failure", message="Error processing request", error={"code": 400, "description": "Bad Request"})
# print(error_response)  # Output: Response(status='failure', message='Error processing request', data={}, error={'code': 400, 'description': 'Bad Request'})
#
# # Serializing to JSON
# success_json = success_response.to_json()
# print(success_json)  # Output: {"status": "success", "message": "Request processed successfully", "data": {"key": "value"}, "error": {}}
#
# # Deserializing from JSON
# deserialized_success_response = Response.from_json(success_json)
# print(deserialized_success_response)  # Output: Response(status='success', message='Request processed successfully', data={'key': 'value'}, error={})
