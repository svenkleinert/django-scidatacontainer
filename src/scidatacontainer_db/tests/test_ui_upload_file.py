from django.urls import reverse

import io

from scidatacontainer_db.models import DataSet
from . import TestCase, get_example_zdc, get_example_wo_author_zdc


class UploadTest(TestCase):

    def test_view_url_exists_at_desired_location(self):
        response = self._post("/upload/")
        self.assertContains(response,
                            "No data file found!",
                            count=1,
                            status_code=400)

    def test_view_url_accessible_by_name(self):
        response = self._post(reverse("scidatacontainer_db:ui-fileupload"))
        self.assertContains(response,
                            "No data file found!",
                            count=1,
                            status_code=400)

    def test_http_method(self):
        response = self._post(reverse("scidatacontainer_db:ui-fileupload"))
        self.assertContains(response,
                            "No data file found!",
                            count=1,
                            status_code=400)

        self.client.force_login(self.user)
        response = self.client.get(
                                   reverse("scidatacontainer_db:ui-fileupload")
                                   )
        self.assertEqual(response.status_code, 405)

    def test_upload(self):
        container = get_example_zdc()
        testid = container["content.json"]["uuid"]
        self.assertEqual(len(DataSet.objects.filter(id=testid)), 0)
        b = container.encode()
        response = self._post(reverse("scidatacontainer_db:ui-fileupload"),
                              data={"uploadfile": io.BytesIO(b)}
                              )

        self.assertContains(response,
                            "Upload successful!",
                            count=1,
                            status_code=201)
        self.assertEqual(len(DataSet.objects.filter(id=testid)), 1)

        container = get_example_wo_author_zdc()
        b = container.encode()
        response = self._post(reverse("scidatacontainer_db:ui-fileupload"),
                              data={"uploadfile": io.BytesIO(b)}
                              )
        self.assertContains(response,
                            "'author' is a required property in meta.json.",
                            count=1,
                            status_code=400)
