from django.urls import reverse

import uuid

from . import APITestCase


VIEW_NAME = "scidatacontainer_db:api:dataset-list"


class ApiDataSetListTest(APITestCase):
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
