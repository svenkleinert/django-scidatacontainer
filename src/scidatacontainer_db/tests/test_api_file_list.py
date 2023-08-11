from django.urls import reverse

from . import APITestCase


class ApiFileListTest(APITestCase):
    view_name = "scidatacontainer_db:api:file-list"

    def test_view_url_exists_at_desired_location(self):
        response = self._get("/api/files/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self._get(reverse(self.view_name))
        self.assertEqual(response.status_code, 200)

    def test_http_method(self):
        response = self._get(reverse(self.view_name))
        self.assertEqual(response.status_code, 200)

        response = self._post(reverse(self.view_name))
        self.assertEqual(response.status_code, 405)

        self.client.force_authenticate(self.user)
        response = self.client.put(reverse(self.view_name))
        self.assertEqual(response.status_code, 405)

    def test_file_list(self):
        response = self._get(reverse(self.view_name))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

        self._create_test_dataset()
        response = self._get(reverse(self.view_name))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 4)
