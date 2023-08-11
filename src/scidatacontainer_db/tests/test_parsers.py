from unittest import TestCase

from scidatacontainer_db.parsers import parsers_from_jsonschema,\
                                        _containerType_parser,\
                                        _datetime_parser,\
                                        _keyword_parser,\
                                        _replaces_parser,\
                                        _used_software_parser

from scidatacontainer_db.utils import MetaDBError


class TestJsonSchemaParserExtraction(TestCase):

    def test_extract_string(self):
        d = {
             "properties": {
                            "test": {
                                     "type": "string"
                                     }
                            }
             }

        p = parsers_from_jsonschema(d)
        self.assertDictEqual(p, {"test": str})

    def test_extract_datetime(self):
        d = {
             "properties": {
                            "test": {
                                     "type": "string",
                                     "format": "date-time"
                                     }
                            }
             }

        p = parsers_from_jsonschema(d)
        self.assertDictEqual(p, {"test": _datetime_parser})

    def test_extract_replaces(self):
        d = {
             "properties": {
                            "replaces": {
                                     "type": "string",
                                     "format": "uuid"
                                     }
                            }
             }

        p = parsers_from_jsonschema(d)
        self.assertDictEqual(p, {"replaces": _replaces_parser})

    def test_extract_usedSoftware(self):
        d = {
             "properties": {
                            "usedSoftware": {
                                     "type": "array",
                                     }
                            }
             }

        p = parsers_from_jsonschema(d)
        self.assertDictEqual(p, {"usedSoftware": _used_software_parser})

    def test_extract_keywords(self):
        d = {
             "properties": {
                            "keywords": {
                                     "type": "array",
                                     }
                            }
             }

        p = parsers_from_jsonschema(d)
        self.assertDictEqual(p, {"keywords": _keyword_parser})

    def test_extract_containerType(self):
        d = {
             "properties": {
                            "containerType": {
                                     "type": "object",
                                     }
                            }
             }

        p = parsers_from_jsonschema(d)
        self.assertDictEqual(p, {"containerType": _containerType_parser})

    def test_extract_no_type(self):
        d = {
             "properties": {
                            "test": {
                                     "format": "date-time"
                                     }
                            }
             }

        p = parsers_from_jsonschema(d)
        self.assertDictEqual(p, {})

    def test_extract_unknown_array(self):
        d = {
             "properties": {
                            "test": {
                                     "type": "array"
                                     }
                            }
             }

        with self.assertRaises(MetaDBError) as cm:
            parsers_from_jsonschema(d)

        self.assertEqual(cm.exception.args[0],
                         {"error_code": 500, "msg": "The model version has a" +
                          " property 'test' that is not supported."})

    def test_extract_unknown_object(self):
        d = {
             "properties": {
                            "test": {
                                     "type": "object"
                                     }
                            }
             }

        with self.assertRaises(MetaDBError) as cm:
            parsers_from_jsonschema(d)

        self.assertEqual(cm.exception.args[0],
                         {"error_code": 500, "msg": "The model version has a" +
                          " property 'test' that is not supported."})
