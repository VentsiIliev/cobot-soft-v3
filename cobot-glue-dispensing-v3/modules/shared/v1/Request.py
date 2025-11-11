import json

class Request:
    def __init__(self, req_type: str, action: str, resource: str = None, data: dict = None):
        """
        Initializes a Request object.

        :param req_type: The type of request, e.g., 'GET' or 'POST'.
        :param action: The specific action to be taken, e.g., 'start', 'createWorkpiece'.
        :param resource: The resource that the action is acting upon, e.g., 'robot', 'camera'.
        :param data: The data related to the action (required for POST, optional for GET).
        """
        self.req_type = req_type  # 'GET' or 'POST'
        self.action = action  # Specific action like 'start', 'createWorkpiece', etc.
        self.resource = resource  if resource else "" # e.g., 'robot', 'camera', etc.
        self.data = data if data is not None else {}  # POST data (optional for GET)

    def to_dict(self) -> dict:
        """
        Convert the Request object to a dictionary for easy serialization (e.g., JSON).

        :return: Dictionary representation of the Request.
        """
        return {
            "type": self.req_type,
            "action": self.action,
            "resource": self.resource,
            "data": self.data
        }

    def to_json(self) -> str:
        """
        Convert the Request object to a JSON string.

        :return: JSON string representation of the Request.
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, request_dict: dict):
        """
        Create a Request object from a dictionary.

        :param request_dict: The dictionary representation of the request.
        :return: A Request object.
        """
        return cls(
            req_type=request_dict.get("type"),
            action=request_dict.get("action"),
            resource=request_dict.get("resource"),
            data=request_dict.get("data")
        )

    @classmethod
    def from_json(cls, request_json: str):
        """
        Create a Request object from a JSON string.

        :param request_json: The JSON string representation of the request.
        :return: A Request object.
        """
        request_dict = json.loads(request_json)
        return cls.from_dict(request_dict)

    def __repr__(self):
        """
        Return a string representation of the Request object.
        """
        return f"Request(type='{self.req_type}', action='{self.action}', resource='{self.resource}', data={self.data})"


