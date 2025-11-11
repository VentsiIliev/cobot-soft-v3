"""
* File: JsonHandler.py
* Author: IlV
* Comments:
* Revision history:
* Date       Author      Description
* -----------------------------------------------------------------
** 130524     IlV         Initial release
* -----------------------------------------------------------------
*
"""

import json


class JsonHandler:
    """
    A class used to handle JSON file operations.

    Attributes
    ----------
    file_path : str
        The path to the JSON file.
    encoder : json.JSONEncoder, optional
        The JSON encoder to use (default is json.JSONEncoder).

    Methods
    -------
    read_json():
        Reads and returns the data from the JSON file.
    write_json(data):
        Writes the given data to the JSON file.
    update_json(new_data):
        Updates the JSON file with the given new data.
    """

    def __init__(self, filePath, encoder=None):
        """
        Constructs all the necessary attributes for the JsonHandler object.

        Parameters
        ----------
        filePath : str
            The path to the JSON file.
        encoder : json.JSONEncoder, optional
            The JSON encoder to use (default is json.JSONEncoder).
        """
        self.file_path = filePath
        self.encoder = encoder if encoder else json.JSONEncoder

    def readJson(self):
        """
        Reads and returns the data from the JSON file.

        Returns
        -------
        dict
            The data from the JSON file, or an empty dictionary if the file is empty.
        """
        with open(self.file_path, 'r') as json_file:
            try:
                data = json.load(json_file)
            except json.JSONDecodeError:
                data = {}
        return data

    def writeJson(self, data):
        """
        Writes the given data to the JSON file.

        Parameters
        ----------
        data : dict
            The data to write to the JSON file.
        """
        with open(self.file_path, 'w') as json_file:
            json.dump(data, json_file, cls=self.encoder, indent=4)

    def updateJson(self, newData):
        """
        Updates the JSON file with the given new data.

        Parameters
        ----------
        newData : dict
            The new data to update the JSON file with.
        """
        data = self.readJson()
        data.update(newData)
        self.writeJson(data)
