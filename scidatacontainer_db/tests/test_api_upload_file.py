from django.contrib.auth.models import User
from django.urls import reverse

from scidatacontainer_db.models import DataSet

from rest_framework.test import APITestCase
from . import TESTDIR

VIEW_NAME = "scidatacontainer_db:api:dataset-list"


class ApiUploadTest(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user("testuser")

    def _post(self, url, **kwargs):
        self.client.force_authenticate(self.user)
        response = self.client.post(url, **kwargs)
        return response

    def test_view_url_exists_at_desired_location(self):
        response = self._post("/api/datasets/")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.reason_phrase,
                         "No data file found in your request!")

    def test_view_url_accessible_by_name(self):
        response = self._post(reverse(VIEW_NAME))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.reason_phrase,
                         "No data file found in your request!")

    def test_http_method(self):
        response = self._post(reverse(VIEW_NAME))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.reason_phrase,
                         "No data file found in your request!")

    def test_upload(self):
        testid = "a31cb576-494f-40c9-af95-e756271278c3"
        self.assertEqual(len(DataSet.objects.filter(id=testid)), 0)
        response = self._post(reverse(VIEW_NAME),
                              data={"uploadfile":
                                    open(TESTDIR + "example.zdc", "rb")
                                    }
                              )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(DataSet.objects.filter(id=testid)), 1)

        response = self._post(reverse(VIEW_NAME),
                              data={"uploadfile":
                                    open(TESTDIR + "example_wo_author.zdc",
                                         "rb")
                                    }
                              )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.reason_phrase,
                         "Attribute 'author' required in meta.json.")

    def test_update(self):
        testid = "a31cb576-494f-40c9-af95-e756271278c3"
        self.assertEqual(len(DataSet.objects.filter(id=testid)), 0)
        response = self._post(reverse(VIEW_NAME),
                              data={"uploadfile":
                                    open(TESTDIR + "example_update.zdc",
                                         "rb")
                                    }
                              )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(DataSet.objects.filter(id=testid)), 1)

        response = self._post(reverse(VIEW_NAME),
                              data={"uploadfile":
                                    open(TESTDIR + "example_update.zdc",
                                         "rb")
                                    }
                              )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(DataSet.objects.filter(id=testid)), 1)

    def test_static_conflict(self):
        self.assertEqual(len(DataSet.objects.all()), 0)
        response = self._post(reverse(VIEW_NAME),
                              data={"uploadfile":
                                    open(TESTDIR + "example_static.zdc",
                                         "rb")
                                    }
                              )
        self.assertEqual(len(DataSet.objects.all()), 1)

        response = self._post(reverse(VIEW_NAME),
                              data={"uploadfile":
                                    open(TESTDIR + "example_static.zdc",
                                         "rb")
                                    }
                              )
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.reason_phrase,
                         "A static file requires a unique hash, but there is" +
                         " already a file with the same hash and UUID=" +
                         "a31cb576-494f-40c9-af95-e756271278c3.")
