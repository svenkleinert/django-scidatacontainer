from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

import hashlib

from scidatacontainer_db.models import DataSet
from . import TESTDIR


class IndexTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user("testuser")

    def _post(self, url, **kwargs):
        self.client.force_login(self.user)
        response = self.client.post(url, **kwargs)
        return response

    def _get(self, url, **kwargs):
        self.client.force_login(self.user)
        response = self.client.get(url, **kwargs)
        return response

    def _create_test_dataset(self):
        filename = TESTDIR + "example.zdc"
        response = self._post(reverse("scidatacontainer_db:ui-fileupload"),
                              data={"uploadfile":
                                    open(filename, "rb")
                                    }
                              )
        self.assertEqual(response.status_code, 201)
        self.id = DataSet.objects.all()[0].id
        self.hash = hashlib.sha256(open(filename, "rb").read()).hexdigest()

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
        self.assertContains(response,
                            "<td>myImage</td>",
                            count=1,
                            status_code=200)

        response = self._get(reverse("scidatacontainer_db:ui-index"),
                             data={"search": "myImage"})
        self.assertContains(response,
                            "<td>myImage</td>",
                            count=1,
                            status_code=200)

        response = self._get(reverse("scidatacontainer_db:ui-index"),
                             data={"search": "mymage"})
        self.assertContains(response,
                            "<td>myImage</td>",
                            count=0,
                            status_code=200)
