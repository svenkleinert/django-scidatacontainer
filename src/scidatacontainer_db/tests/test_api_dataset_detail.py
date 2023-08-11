from django.urls import reverse

import io
import uuid

from scidatacontainer_db.models import DataSet, DataSetBase
from . import APITestCase, get_example_replaces_zdc


class ApiDataSetDetailTest(APITestCase):
    view_name = "scidatacontainer_db:api:dataset-detail"

    def test_view_url_exists_at_desired_location(self):
        self._create_test_dataset()
        response = self._get("/api/datasets/" + str(self.id) + "/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        self._create_test_dataset()
        response = self._get(reverse(self.view_name, args=[str(self.id)]))
        self.assertEqual(response.status_code, 200)

    def test_http_method(self):
        self._create_test_dataset()
        response = self._get(reverse(self.view_name, args=[str(self.id)]))
        self.assertEqual(response.status_code, 200)

        response = self._post(reverse(self.view_name, args=[str(self.id)]))
        self.assertEqual(response.status_code, 405)

        self.client.force_authenticate(self.user)
        response = self.client.put(reverse(self.view_name,
                                           args=[str(self.id)]))
        self.assertEqual(response.status_code, 405)

    def test_dataset_detail(self):
        rand_id = str(uuid.uuid4())
        response = self._get(reverse(self.view_name, args=[rand_id]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.reason_phrase,
                         "No DataSet with UUID=" + rand_id + " found!")

        self._create_test_dataset()
        response = self._get(reverse(self.view_name, args=[str(self.id)]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["uuid"], str(self.id))

    def test_replaced_by(self):
        self._create_test_dataset()

        dataset = DataSet.objects.get(id=self.id)
        self.assertFalse(dataset.is_replaced)
        self.assertEqual(dataset.replaced_by, None)

        b = io.BytesIO(get_example_replaces_zdc().encode())

        response = self._post(reverse("scidatacontainer_db:api:dataset-list"),
                              data={"uploadfile": b}
                              )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(DataSet.objects.all()), 2)

        dataset = DataSet.objects.get(id=self.id)
        self.assertTrue(dataset.is_replaced)
        self.assertNotEqual(dataset.replaced_by, None)
        self.assertTrue(isinstance(dataset.replaced_by, DataSetBase))

        response = self._get(reverse(self.view_name, args=[str(self.id)]))
        self.assertEqual(response.status_code, 301)
        self.assertNotEqual(response.data["uuid"], str(self.id))

        url = reverse("scidatacontainer_db:api:dataset-detail-noredirect",
                      args=[str(self.id)])
        response = self._get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["uuid"], str(self.id))

    def test_invalid(self):
        self._create_test_dataset()
        dataset = DataSet.objects.get(id=self.id)
        self.assertTrue(dataset.valid)

        dataset.valid = False
        dataset.save()
        response = self._get(reverse(self.view_name, args=[str(self.id)]))

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.reason_phrase, "DataSet was deleted!")
