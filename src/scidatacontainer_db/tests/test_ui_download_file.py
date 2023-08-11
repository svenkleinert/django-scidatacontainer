from django.urls import reverse

import hashlib
import uuid

from . import TestCase


class DownloadTest(TestCase):

    def test_view_url_exists_at_desired_location(self):
        self._create_test_dataset()
        response = self._get("/download/" + str(self.id))
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        self._create_test_dataset()
        response = self._get(reverse("scidatacontainer_db:ui-filedownload",
                                     args=[str(self.id)]))
        self.assertEqual(response.status_code, 200)

    def test_http_method(self):
        self._create_test_dataset()
        response = self._get(reverse("scidatacontainer_db:ui-filedownload",
                                     args=[str(self.id)]))
        self.assertEqual(response.status_code, 200)

        response = self._post(reverse("scidatacontainer_db:ui-filedownload",
                                      args=[str(self.id)]))
        self.assertEqual(response.status_code, 405)

    def test_download(self):
        self._create_test_dataset()

        response = self._get(reverse("scidatacontainer_db:ui-filedownload",
                                     args=[str(self.id)]))
        self.assertEqual(response.status_code, 200)
        file_content = b"".join(response.streaming_content)
        return_hash = hashlib.sha256(file_content).hexdigest()

        self.assertEqual(self.hash, return_hash)

        response = self._get(reverse("scidatacontainer_db:ui-filedownload",
                                     args=[str(uuid.uuid4())]))
        self.assertContains(response,
                            "Not Found",
                            status_code=404)
