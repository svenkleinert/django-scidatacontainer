from django.contrib.auth.models import User
from django.urls import reverse

import hashlib
import uuid

from scidatacontainer_db.models import DataSet, DataSetBase
from . import TESTDIR

from rest_framework.test import APITestCase

VIEW_NAME = "scidatacontainer_db:api:dataset-detail"


class ApiDataSetDetailTest(APITestCase):

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
        self._create_test_dataset()
        response = self._get("/api/datasets/" + str(self.id) + "/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        self._create_test_dataset()
        response = self._get(reverse(VIEW_NAME, args=[str(self.id)]))
        self.assertEqual(response.status_code, 200)

    def test_http_method(self):
        self._create_test_dataset()
        response = self._get(reverse(VIEW_NAME, args=[str(self.id)]))
        self.assertEqual(response.status_code, 200)

        response = self._post(reverse(VIEW_NAME, args=[str(self.id)]))
        self.assertEqual(response.status_code, 405)

        self.client.force_authenticate(self.user)
        response = self.client.put(reverse(VIEW_NAME, args=[str(self.id)]))
        self.assertEqual(response.status_code, 405)

    def test_dataset_detail(self):
        rand_id = str(uuid.uuid4())
        response = self._get(reverse(VIEW_NAME, args=[rand_id]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.reason_phrase,
                         "No DataSet with UUID=" + rand_id + " found!")

        self._create_test_dataset()
        response = self._get(reverse(VIEW_NAME, args=[str(self.id)]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], str(self.id))

    def test_replaced_by(self):
        self._create_test_dataset()

        dataset = DataSet.objects.get(id=self.id)
        self.assertFalse(dataset.is_replaced)
        self.assertEqual(dataset.replaced_by, None)

        filename = TESTDIR + "example_replaces.zdc"
        response = self._post(reverse("scidatacontainer_db:api:dataset-list"),
                              data={"uploadfile":
                                    open(filename, "rb")
                                    }
                              )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(DataSet.objects.all()), 2)

        dataset = DataSet.objects.get(id=self.id)
        self.assertTrue(dataset.is_replaced)
        self.assertNotEqual(dataset.replaced_by, None)
        self.assertTrue(isinstance(dataset.replaced_by, DataSetBase))

        response = self._get(reverse(VIEW_NAME, args=[str(self.id)]))
        self.assertEqual(response.status_code, 301)
        self.assertNotEqual(response.data["id"], str(self.id))

        url = reverse("scidatacontainer_db:api:dataset-detail-noredirect",
                      args=[str(self.id)])
        response = self._get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], str(self.id))

    def test_invalid(self):
        self._create_test_dataset()
        dataset = DataSet.objects.get(id=self.id)
        self.assertTrue(dataset.valid)

        dataset.valid = False
        dataset.save()
        response = self._get(reverse(VIEW_NAME, args=[str(self.id)]))

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.reason_phrase, "DataSet was deleted!")
