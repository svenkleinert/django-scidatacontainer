from django.test import LiveServerTestCase
from django.contrib.auth.models import User

from knox.models import AuthToken

from scidatacontainer.tests.test_upload import _TestUpload
from scidatacontainer.tests.test_download import _TestDownload


class TestClientUpload(LiveServerTestCase, _TestUpload):
    __test__ = True

    def setUp(self):
        self.user = User.objects.create_user("testuser")
        self.api_key = AuthToken.objects.create(self.user)[1]


class TestClientDownload(LiveServerTestCase, _TestDownload):
    __test__ = True

    def setUp(self):
        self.user = User.objects.create_user("testuser")
        self.api_key = AuthToken.objects.create(self.user)[1]
