import unittest
from unittest.mock import patch
import requests
import app
import json

class TestApp(unittest.TestCase):
    def test_validate_ok(self):
        data = {"category": "billing", "priority": "high", "summary": "test", "tags": [], "requires_human": True}
        self.assertEqual(app.parse_and_validate({"choices": [{"message": {"content": json.dumps(data)}}]}), data)

    def test_validate_missing(self):
        with self.assertRaises(ValueError):
            app.parse_and_validate({"choices": [{"message": {"content": '{"category": "billing"}'}}]})

if __name__ == "__main__":
    unittest.main()