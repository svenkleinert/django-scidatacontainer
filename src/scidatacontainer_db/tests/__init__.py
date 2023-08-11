from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
import django.test
from django.urls import reverse

from scidatacontainer_db.models import DataSet

import datetime
import io
import hashlib
import mimetypes
import os
import uuid

import rest_framework.test
from scidatacontainer.tests import get_test_container

TESTDIR = os.path.dirname(os.path.abspath(__file__)) + "/"

testuuid = str(uuid.uuid4())


def get_example_zdc():
    container = get_test_container()
    # non default uuid required, otherwise it is not stored
    container["content.json"]["uuid"] = testuuid
    container["meta.json"]["doi"] = "https://example.com/" + testuuid
    container["content.json"]["complete"] = False
    return container


def get_example_faulty_zdc():
    container = get_example_zdc()
    container["content.json"]["storageTime"] = str(datetime.date.today())
    return container


def get_example_faulty_id_zdc():
    container = get_example_zdc()
    container["content.json"]["uuid"] = testuuid[:-4]
    return container


def get_example_replaces_zdc():
    container = get_example_zdc()
    container["content.json"]["uuid"] = str(uuid.uuid4())
    container["content.json"]["replaces"] = testuuid
    return container


def get_example_static_zdc():
    container = get_example_zdc()
    container.freeze()
    return container


def get_example_static_wo_hash_zdc():
    container = get_example_static_zdc()
    del container["content.json"]["hash"]
    return container


def get_example_static_wrong_hash_zdc():
    container = get_example_static_zdc()
    container["content.json"]["hash"] = None
    return container


def get_example_update_zdc():
    container = get_example_zdc()
    t_old = container["content.json"]["storageTime"]
    t = datetime.datetime.fromisoformat(t_old)
    t += datetime.timedelta(seconds=1)
    container["content.json"]["storageTime"] = t.isoformat(timespec='seconds')
    container["content.json"]["containerType"]["name"] = "TestType2"
    return container


def get_example_version_zdc():
    container = get_example_zdc()
    container["content.json"]["modelVersion"] = "0.2"
    return container


def get_example_wo_author_zdc():
    container = get_example_zdc()
    del container["meta.json"]["author"]
    return container


def get_example_wo_complete_zdc():
    container = get_example_zdc()
    del container["content.json"]["complete"]
    return container


class TestCase(django.test.TestCase):
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

    def _create_temp_from_container(self, container):
        def getsize(f):
            f.seek(0)
            f.read()
            s = f.tell()
            f.seek(0)
            return s

        name = container["content.json"]["uuid"] + ".zdc"
        content_type, charset = mimetypes.guess_type(name)
        size = getsize(io.BytesIO(container.encode()))

        file = InMemoryUploadedFile(file=io.BytesIO(container.encode()),
                                    name=name,
                                    field_name=None, content_type=content_type,
                                    charset=charset, size=size)
        return file

    def _create_test_dataset(self):
        self.container = get_example_zdc()
        b = self.container.encode()
        response = self._post(reverse("scidatacontainer_db:ui-fileupload"),
                              data={"uploadfile": io.BytesIO(b)})
        self.assertEqual(response.status_code, 201)
        self.id = DataSet.objects.all()[0].id
        self.hash = hashlib.sha256(b).hexdigest()
        self.perm_url = reverse("scidatacontainer_db:ui-permission_update",
                                args=[str(self.id)])


class APITestCase(rest_framework.test.APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user("testuser")

    def _post(self, url, **kwargs):
        self.client.force_authenticate(self.user)
        response = self.client.post(url, **kwargs)
        return response

    def _get(self, url, **kwargs):
        self.client.force_authenticate(self.user)
        response = self.client.get(url, **kwargs)
        return response

    def _create_test_dataset(self):
        self.container = get_example_zdc()
        b = self.container.encode()
        response = self._post(reverse("scidatacontainer_db:api:dataset-list"),
                              data={"uploadfile": io.BytesIO(b)}
                              )
        self.assertEqual(response.status_code, 201)
        self.id = DataSet.objects.all()[0].id
        self.hash = hashlib.sha256(b).hexdigest()
