"""
Description:
    Interface for JSON serialization and deserialization of objects.
    Classes that inherit from JsonSerializable should implement methods
    to convert themselves to/from JSON-compatible formats.
"""

from typing import Dict, Any

class JsonSerializable:
    """
       A base class for defining JSON-serializable objects. Subclasses should
       implement methods to convert objects to dictionaries and to instantiate
       objects from dictionaries.

       This interface helps standardize the process of serializing domain objects
       to JSON and deserializing them from JSON across the application.
       """
    def to_json(self) -> Dict[str, Any]:
        """
              Converts the current object instance into a JSON-serializable dictionary.

              Returns:
                  Dict[str, Any]: A dictionary representing the object suitable for
                  JSON serialization (e.g., for saving to a file or sending over a network).

              Raises:
                  NotImplementedError: If not overridden in subclass.
              """
        pass

    @staticmethod
    def deserialize(json: Dict[str, Any]) -> 'JsonSerializable':
        """
               Reconstructs an object from a dictionary (typically parsed from JSON).

               Args:
                   json (Dict[str, Any]): A dictionary containing the serialized data.

               Returns:
                   JsonSerializable: An instance of a subclass of JsonSerializable
                   constructed from the dictionary.

               Raises:
                   NotImplementedError: If not overridden in subclass.
               """
        pass

    @staticmethod
    def serialize(self) -> str:
        """
                Converts the object instance into a JSON-compatible string format.

                Args:
                    self (JsonSerializable): The object to serialize.

                Returns:
                    str: A JSON string representation of the object.

                Raises:
                    NotImplementedError: If not overridden in subclass.
                """
        pass