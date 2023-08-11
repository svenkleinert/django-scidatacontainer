from django.urls import reverse

import io

from scidatacontainer_db.models import DataSet
from . import TestCase, get_example_replaces_zdc


class DetailTest(TestCase):

    def test_view_url_exists_at_desired_location(self):
        self._create_test_dataset()
        response = self._get("/" + str(self.id) + "/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        self._create_test_dataset()
        response = self._get(reverse("scidatacontainer_db:ui-detail",
                                     args=[str(self.id)]))
        self.assertEqual(response.status_code, 200)

    def test_http_method(self):
        self._create_test_dataset()
        response = self._get(reverse("scidatacontainer_db:ui-detail",
                                     args=[str(self.id)]))
        self.assertEqual(response.status_code, 200)

        response = self._post(reverse("scidatacontainer_db:ui-detail",
                                      args=[str(self.id)]))
        self.assertEqual(response.status_code, 405)

    def test_template(self):
        self._create_test_dataset()
        response = self._get(reverse("scidatacontainer_db:ui-detail",
                                     args=[str(self.id)]))
        self.assertTemplateUsed(response, "scidatacontainer_db/detail.html")

    def test_valid_warning(self):
        self._create_test_dataset()
        obj = DataSet.objects.get(id=self.id)
        obj.valid = False
        obj.save()
        response = self._get(reverse("scidatacontainer_db:ui-detail",
                                     args=[str(self.id)]))

        self.assertContains(response,
                            "WARNING: This dataset is marked invalid.")

        obj.invalidation_comment = "Testreason"
        obj.save()

        response = self._get(reverse("scidatacontainer_db:ui-detail",
                                     args=[str(self.id)]))

        self.assertContains(response,
                            "WARNING: This dataset is marked invalid due to " +
                            "the following reason: Testreason")

    def test_invalidation(self):
        self._create_test_dataset()

        response = self._post(reverse("scidatacontainer_db:ui-delete",
                                      args=[str(self.id)]))
        self.assertEqual(response.status_code, 405)

        response = self._post(reverse("scidatacontainer_db:ui-delete",
                                      args=[str(self.id)]),
                              data={"_method": "patch"})

        self.assertRedirects(response, reverse("scidatacontainer_db:ui-detail",
                                               args=[str(self.id)]))

        response = self._post(reverse("scidatacontainer_db:ui-delete",
                                      args=[str(self.id)]),
                              data={"_method": "patch",
                                    "confirm": True,
                                    "reason": "Testreason"},
                              follow=True)

        self.assertRedirects(response, reverse("scidatacontainer_db:ui-index"))
        self.assertContains(response,
                            "Dataset " + str(self.id) + " was deleted.")

        obj = DataSet.objects.get(id=self.id)
        self.assertFalse(obj.valid)
        self.assertEqual(obj.invalidation_comment, "Testreason")

    def test_replaced(self):
        self._create_test_dataset()
        b = get_example_replaces_zdc().encode()
        response = self._post(reverse("scidatacontainer_db:ui-fileupload"),
                              data={"uploadfile":
                                    io.BytesIO(b)
                                    }
                              )
        self.assertEqual(response.status_code, 201)

        dc1 = DataSet.objects.get(id=self.id)
        dc2 = DataSet.objects.exclude(id=self.id)[0]

        response = self._get(reverse("scidatacontainer_db:ui-detail",
                                     args=[str(self.id)]))
        self.assertEqual(response.status_code, 302)

        response = self._get(reverse("scidatacontainer_db:ui-detail",
                                     args=[str(self.id)]), follow=True)
        self.assertContains(response,
                            "The dataset with UUID=" + str(dc1.id) +
                            " was replaced by the dataset with UUID=" +
                            str(dc2.id) + ". You were " +
                            "automatically redirected.",
                            status_code=200)
