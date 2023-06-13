from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from scidatacontainer_db.models import DataSet
from . import TESTDIR


class UploadTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user("testuser")

    def _post(self, url, **kwargs):
        self.client.force_login(self.user)
        response = self.client.post(url, **kwargs)
        return response

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
        testid = "a31cb576-494f-40c9-af95-e756271278c3"
        self.assertEqual(len(DataSet.objects.filter(id=testid)), 0)
        filename = TESTDIR + "example.zdc"
        response = self._post(reverse("scidatacontainer_db:ui-fileupload"),
                              data={"uploadfile": open(filename, "rb")}
                              )

        self.assertContains(response,
                            "Upload successful!",
                            count=1,
                            status_code=201)
        self.assertEqual(len(DataSet.objects.filter(id=testid)), 1)

        filename = TESTDIR + "example_wo_author.zdc"
        response = self._post(reverse("scidatacontainer_db:ui-fileupload"),
                              data={"uploadfile": open(filename, "rb")}
                              )

        self.assertContains(response,
                            "Attribute 'author' required in meta.json.",
                            count=1,
                            status_code=400)
