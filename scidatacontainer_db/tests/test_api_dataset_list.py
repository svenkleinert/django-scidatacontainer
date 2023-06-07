from django.contrib.auth.models import User
from django.urls import reverse

import hashlib
import uuid

from scidatacontainer_db.models import DataSet
from . import TESTDIR

from rest_framework.test import APITestCase

VIEW_NAME = "scidatacontainer_db:api:dataset-list"


class ApiDataSetListTest(APITestCase):

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
        response = self._post(reverse(VIEW_NAME),
                              data={"uploadfile":
                                    open(filename, "rb")
                                    }
                              )
        self.assertEqual(response.status_code, 201)
        self.id = DataSet.objects.all()[0].id
        self.hash = hashlib.sha256(open(filename, "rb").read()).hexdigest()

    def test_view_url_exists_at_desired_location(self):
        response = self._get("/api/datasets/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self._get(reverse(VIEW_NAME))
        self.assertEqual(response.status_code, 200)

    def test_http_method(self):
        response = self._get(reverse(VIEW_NAME))
        self.assertEqual(response.status_code, 200)

    def test_dataset_list(self):
        response = self._get(reverse(VIEW_NAME))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

        self._create_test_dataset()
        response = self._get(reverse(VIEW_NAME))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_dataset_filter(self):
        self.test_dataset_list()

        response = self._get(reverse(VIEW_NAME),
                             data={"id": self.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        response = self._get(reverse(VIEW_NAME),
                             data={"id": uuid.uuid4()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

        response = self._get(reverse(VIEW_NAME),
                             data={"title__contains": "image"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        response = self._get(reverse(VIEW_NAME),
                             data={"title__contains": "42"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)
