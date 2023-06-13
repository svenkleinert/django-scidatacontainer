from django.contrib.auth.models import User
from django.urls import reverse

import hashlib

from scidatacontainer_db.models import DataSet
from . import TESTDIR

from rest_framework.test import APITestCase

VIEW_NAME = "scidatacontainer_db:api:file-list"


class ApiFileListTest(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user("testuser")

    def _post(self, url, **kwargs):
        self.client.force_authenticate(self.user)
        response = self.client.post(url, **kwargs)
        return response

    def _get(self, url, **kwargs):
        self.client.force_authenticate(self.user)
        response = self.client.get(url, **kwargs)
        return response

    def _create_test_dataset(self):
        filename = TESTDIR + "example.zdc"
        response = self._post(reverse("scidatacontainer_db:api:dataset-list"),
                              data={"uploadfile":
                                    open(filename, "rb")
                                    }
                              )
        self.assertEqual(response.status_code, 201)
        self.id = DataSet.objects.all()[0].id
        self.hash = hashlib.sha256(open(filename, "rb").read()).hexdigest()

    def test_view_url_exists_at_desired_location(self):
        response = self._get("/api/files/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self._get(reverse(VIEW_NAME))
        self.assertEqual(response.status_code, 200)

    def test_http_method(self):
        response = self._get(reverse(VIEW_NAME))
        self.assertEqual(response.status_code, 200)

        response = self._post(reverse(VIEW_NAME))
        self.assertEqual(response.status_code, 405)

        self.client.force_authenticate(self.user)
        response = self.client.put(reverse(VIEW_NAME))
        self.assertEqual(response.status_code, 405)

    def test_file_list(self):
        response = self._get(reverse(VIEW_NAME))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

        self._create_test_dataset()
        response = self._get(reverse(VIEW_NAME))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 4)
