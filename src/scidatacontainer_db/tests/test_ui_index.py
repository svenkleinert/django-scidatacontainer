from django.urls import reverse

from . import TestCase


class IndexTest(TestCase):

    def test_view_url_exists_at_desired_location(self):
        self._create_test_dataset()
        response = self._get("/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        self._create_test_dataset()
        response = self._get(reverse("scidatacontainer_db:ui-index"))
        self.assertEqual(response.status_code, 200)

    def test_http_method(self):
        self._create_test_dataset()
        response = self._get(reverse("scidatacontainer_db:ui-index"))
        self.assertEqual(response.status_code, 200)

        response = self._post(reverse("scidatacontainer_db:ui-index"))
        self.assertEqual(response.status_code, 405)

    def test_template(self):
        self._create_test_dataset()
        response = self._get(reverse("scidatacontainer_db:ui-index"))
        self.assertTemplateUsed(response, "scidatacontainer_db/index.html")

    def test_search(self):
        self._create_test_dataset()
        response = self._get(reverse("scidatacontainer_db:ui-index"))
        ct_name = self.container["content.json"]["containerType"]["name"]
        ct_version = self.container["content.json"]["containerType"]["version"]
        self.assertContains(response,
                            "<td>" + ct_name + ", v" + ct_version + "</td>",
                            count=1,
                            status_code=200)

        response = self._get(reverse("scidatacontainer_db:ui-index"),
                             data={"search": "TestType"})
        self.assertContains(response,
                            "<td>" + ct_name + ", v" + ct_version + "</td>",
                            count=1,
                            status_code=200)

        response = self._get(reverse("scidatacontainer_db:ui-index"),
                             data={"search": "TestTpe"})
        self.assertContains(response,
                            "<td>" + ct_name + ", v" + ct_version + "</td>",
                            count=0,
                            status_code=200)
