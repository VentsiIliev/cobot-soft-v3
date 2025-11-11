"""
* File: test_JsonHandler.py
* Author: IlV
* Comments:
* Revision history:
* Date       Author      Description
* -----------------------------------------------------------------
** 130524     IlV         Initial release
* -----------------------------------------------------------------
*
"""

import unittest
import os
import json

from PLVision.JsonHandler import JsonHandler


class TestJsonHandler(unittest.TestCase):
    def setUp(self):
        self.jsonHandler = JsonHandler('testData/test.json')
        with open('testData/test.json', 'w') as f:
            json.dump({"key": "value"}, f)

    def test_read_json(self):
        data = self.jsonHandler.read_json()
        self.assertEqual(data, {"key": "value"})

    def test_read_json_missing_file(self):
        jsonHandler = JsonHandler('testData/missing.json')
        with self.assertRaises(FileNotFoundError):
            jsonHandler.read_json()

    def test_write_json(self):
        self.jsonHandler.write_json({"key": "value"})

        with open('testData/test.json', 'r') as f:
            data = json.load(f)

        self.assertEqual(data, {"key": "value"})

    def test_write_json_creates_file(self):
        jsonHandler = JsonHandler('testData/missing.json')
        jsonHandler.write_json({"key": "value"})
        self.assertTrue(os.path.exists('testData/missing.json'))
        if os.path.exists('testData/missing.json'):
            os.remove('testData/missing.json')

    def test_update_json(self):
        with open('testData/test.json', 'w') as f:
            json.dump({"key": "value"}, f)

        self.jsonHandler.update_json({"new_key": "new_value"})

        with open('testData/test.json', 'r') as f:
            data = json.load(f)

        self.assertEqual(data, {"key": "value", "new_key": "new_value"})

    def test_update_json_missing_file(self):
        jsonHandler = JsonHandler('testData/missing.json')
        with self.assertRaises(FileNotFoundError):
            jsonHandler.update_json({"key": "value"})


if __name__ == '__main__':
    unittest.main()
