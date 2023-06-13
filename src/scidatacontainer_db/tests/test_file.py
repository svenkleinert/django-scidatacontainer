from django.test import TestCase
import json
from scidatacontainer_db.models import File


class FileTest(TestCase):

    def test_file_creation(self):
        f = File(name="Testfile", size=200)
        f.save()
        self.assertTrue(isinstance(f, File))
        self.assertEqual(f.name, "Testfile")

        json_str = """
{
  "firstName": "John",
  "lastName": "Smith",
  "isAlive": true,
  "age": 27,
  "address": {
    "streetAddress": "21 2nd Street",
    "city": "New York",
    "state": "NY",
    "postalCode": "10021-3100"
  },
  "phoneNumbers": [
    {
      "type": "home",
      "number": "212 555-1234"
    },
    {
      "type": "office",
      "number": "646 555-4567"
    }
  ],
  "children": [
      "Catherine",
      "Thomas",
      "Trevor"
  ],
  "spouse": null
}"""
        f_json = File(name="test.json", size=200, content=json.loads(json_str))
        f_json.save()
        self.assertTrue(isinstance(f_json, File))
        self.assertEqual(f_json.name, "test.json")
        self.assertEqual(f_json.content["firstName"], "John")
        self.assertEqual(f_json.content["lastName"], "Smith")
        self.assertEqual(f_json.content["isAlive"], True)
        self.assertEqual(f_json.content["age"], 27)
        self.assertEqual(f_json.content["address"]["state"], "NY")
        self.assertEqual(f_json.content["phoneNumbers"][0]["type"], "home")
        self.assertEqual(len(f_json.content["phoneNumbers"]), 2)
