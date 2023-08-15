from django.contrib.auth.models import User
from django.urls import reverse

from scidatacontainer_db.urls import urlpatterns

import unittest

from rest_framework.test import APITestCase


class ApiOverviewTest(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user("testuser")

    def _get(self, url, **kwargs):
        self.client.force_authenticate(self.user)
        response = self.client.get(url, **kwargs)
        return response

    def test_view_url_exists_at_desired_location(self):
        response = self._get("/api/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self._get(reverse("scidatacontainer_db:api:api-root"))
        self.assertEqual(response.status_code, 200)

    def test_http_methd(self):
        response = self._get(reverse("scidatacontainer_db:api:api-root"))
        self.assertEqual(response.status_code, 200)

        self.client.force_authenticate(self.user)
        response = self.client.post(
                                    reverse("scidatacontainer_db:api:api-root")
                                    )
        self.assertEqual(response.status_code, 405)

    @unittest.skip("ToDo: Not working with Swagger overview.")
    def test_api_overview(self):
        response = self._get(reverse("scidatacontainer_db:api:api-root"))
        content = response.content.decode("utf-8")
        for url in urlpatterns:
            route = url.pattern._route
            if route.startswith("api"):
                route = route.replace("<drf_format_suffix_json_html:format>",
                                      ".json")
                if not route.endswith(".json"):
                    self.assertIn(route, content)
