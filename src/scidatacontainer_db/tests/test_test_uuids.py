from django.urls import reverse

import io
import json
import unittest
from uuid import UUID

from . import APITestCase, get_example_zdc

from scidatacontainer.tests import get_test_container

import iso8601


class TestUUIDDownloadTest(APITestCase):
    view_name = "scidatacontainer_db:api:dataset-download"

    def test_dowload_zero_uuid(self):
        uuid = UUID(int=0)
        response = self._get(reverse(self.view_name,
                                     args=[str(uuid)]))
        self.assertEqual(response.status_code, 200)
        c = get_test_container()
        c["meta.json"]["author"] = ""
        c.decode(b''.join(response.streaming_content))
        self.assertEqual(c["meta.json"]["author"], "John Doe")

    def test_dowload_deleted_uuid(self):
        uuid = UUID(int=0x204)
        response = self._get(reverse(self.view_name,
                                     args=[str(uuid)]))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.reason_phrase, "DataSet was deleted")

    def test_download_not_found_uuid(self):
        uuid = UUID(int=0x404)
        response = self._get(reverse(self.view_name,
                                     args=[str(uuid)]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.reason_phrase,
                         "No DataSet with UUID=00000000-0000-0000-0000-" +
                         "000000000404 found!")

    def test_download_permission_denied_uuid(self):
        uuid = UUID(int=0x403)
        response = self._get(reverse(self.view_name,
                                     args=[str(uuid)]))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.reason_phrase, "Forbidden")


class TestUUIDUploadTest(APITestCase):
    view_name = "scidatacontainer_db:api:dataset-list"

    def test_upload_test_dataset(self):
        b = io.BytesIO(get_test_container().encode())
        response = self._post(reverse(self.view_name),
                              data={"uploadfile": b})

        self.assertEqual(response.status_code, 201)

    def test_upload_complete_dataset(self):
        c = get_test_container()
        c["content.json"]["uuid"] = str(UUID(int=0x409))
        b = io.BytesIO(c.encode())
        response = self._post(reverse(self.view_name),
                              data={"uploadfile": b})

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.reason_phrase,
                         "Dataset is marked complete. No further changes " +
                         "allowed.")

    def test_upload_permission_denied_dataset(self):
        c = get_test_container()
        c["content.json"]["uuid"] = str(UUID(int=0x403))
        b = io.BytesIO(c.encode())
        response = self._post(reverse(self.view_name),
                              data={"uploadfile": b})

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.reason_phrase,
                         "You don't have permission to update this dataset.")

    def test_upload_static_conflict_dataset(self):
        c = get_test_container()
        c["content.json"]["uuid"] = str(UUID(int=0x400))
        c.freeze()
        b = io.BytesIO(c.encode())
        response = self._post(reverse(self.view_name),
                              data={"uploadfile": b})


        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.reason_phrase,
                         "Existing static dataset with same hash found.")

        self.assertEqual(c["content.json"]["hash"],
                         json.loads(response.content.decode("utf-8"))["hash"])


class TestUUIDApiDetailTest(APITestCase):
    view_name = "scidatacontainer_db:api:dataset-detail"
    def test_detail_zero_uuid(self):
        uuid = UUID(int=0)
        response = self._get(reverse(self.view_name,
                                     args=[str(uuid)]))
        self.assertEqual(response.status_code, 200)
        d = json.loads(response.content.decode("utf-8"))

        c = get_test_container()
        c["content.json"]["uuid"] = str(uuid)
        c["meta.json"]["doi"] = "https://example.com/" + str(uuid)

        for key, value in c["content.json"].items():
            if key == "replaces":
                self.assertEqual(value, d[key]["uuid"])
            elif key == "usedSoftware":
                self.assertEqual(len(value), len(d[key]))
                for s in d[key]:
                    del s["url"]
                    if s["id"] == "":
                        del s["id"]
                    if s["idType"] == "":
                        del s["idType"]
                    self.assertIn(s, value)
            elif key == "containerType":
                del d[key]["url"]
                self.assertDictEqual(value, d[key])
            elif isinstance(value, str):
                if iso8601.is_iso8601(value):
                    self.assertEqual(iso8601.parse_date(value),
                                     iso8601.parse_date(d[key]))
            else:
                self.assertEqual(value, d[key])

        for key, value in c["meta.json"].items():
            if key == "keywords":
                self.assertEqual(len(value), len(d[key]))
                for k in d[key]:
                    self.assertIn(k["name"], value)
            elif isinstance(value, str):
                if iso8601.is_iso8601(value):
                    self.assertEqual(iso8601.parse_date(value),
                                     iso8601.parse_date(d[key]))
            else:
                # might be necessary if data model is extended.
                self.assertEqual(value, d[key]) #  pragma: no cover

    def test_detail_204(self):
        uuid = UUID(int=0x204)
        response = self._get(reverse(self.view_name,
                                     args=[str(uuid)]))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.reason_phrase, "DataSet was deleted")
        self.assertEqual(response.content, b'')

    def test_detail_404(self):
        uuid = UUID(int=0x404)
        response = self._get(reverse(self.view_name,
                                     args=[str(uuid)]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.reason_phrase, "No DataSet with UUID=" +
                                                 str(uuid) + " found!")
        self.assertEqual(response.content, b'')

    def test_detail_403(self):
        uuid = UUID(int=0x403)
        response = self._get(reverse(self.view_name,
                                     args=[str(uuid)]))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.reason_phrase, "Forbidden")
        self.assertEqual(response.content, b'{"detail":"You do not have ' +
                                           b'permission to perform this ' +
                                           b'action."}')

    def test_detail_301(self):
        uuid = UUID(int=0x301)
        response = self._get(reverse(self.view_name,
                                     args=[str(uuid)]))
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.reason_phrase, "Moved Permanently")
        d = json.loads(response.content.decode("utf-8"))
        self.assertEqual(d["replaces"]["uuid"], str(uuid))
