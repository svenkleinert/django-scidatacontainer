from django.contrib.auth.models import Group, User
from django.urls import reverse

import hashlib
import uuid

from guardian.shortcuts import get_objects_for_user, get_objects_for_group

from scidatacontainer_db.models import DataSet
from . import TESTDIR

from rest_framework.test import APITestCase

VIEW_NAME = "scidatacontainer_db:api:dataset-detail"


class ApiDataSetDetailTest(APITestCase):

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

    def _patch(self, url, **kwargs):
        self.client.force_authenticate(self.user)
        response = self.client.patch(url, **kwargs)
        return response

    def _create_test_dataset(self):
        filename = TESTDIR + "example.zdc"
        response = self._post(reverse("scidatacontainer_db:api:dataset-list"),
                              data={"uploadfile":
                                    open(filename, "rb")
                                    }
                              )
        self.assertEqual(response.status_code, 201)
        self.id = DataSet.objects.all()[0].id
        self.hash = hashlib.sha256(open(filename, "rb").read()).hexdigest()

    def test_view_url_exists_at_desired_location(self):
        self._create_test_dataset()
        response = self._patch("/api/datasets/" + str(self.id) + "/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        self._create_test_dataset()
        response = self._patch(reverse(VIEW_NAME, args=[str(self.id)]))
        self.assertEqual(response.status_code, 200)

    def test_http_method(self):
        self._create_test_dataset()
        response = self._get(reverse(VIEW_NAME, args=[str(self.id)]))
        self.assertEqual(response.status_code, 200)

        response = self._patch(reverse(VIEW_NAME, args=[str(self.id)]))
        self.assertEqual(response.status_code, 200)

        response = self._post(reverse(VIEW_NAME, args=[str(self.id)]))
        self.assertEqual(response.status_code, 405)

        self.client.force_authenticate(self.user)
        response = self.client.put(reverse(VIEW_NAME, args=[str(self.id)]))
        self.assertEqual(response.status_code, 405)

    def test_permission(self):
        self._create_test_dataset()
        testuser2 = User.objects.create_user("testuser2")

        rand_username = str(uuid.uuid4())
        response = self._patch(reverse(VIEW_NAME, args=[str(self.id)]),
                               data={"owner": rand_username})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.reason_phrase,
                         "New owner " + rand_username + " does not exist")

        response = self._patch(reverse(VIEW_NAME, args=[str(self.id)]),
                               data={"owner": testuser2.username})
        self.assertEqual(response.status_code, 200)

        response = self._patch(reverse(VIEW_NAME, args=[str(self.id)]))
        self.assertEqual(response.status_code, 403)

    def test_dataset_patch_users(self):
        testuser2 = User.objects.create_user("testuser2")
        testuser3 = User.objects.create_user("testuser3")

        response = self._get(reverse(VIEW_NAME, args=[uuid.uuid4()]))
        self.assertEqual(response.status_code, 404)

        self._create_test_dataset()
        response = self._patch(reverse(VIEW_NAME, args=[str(self.id)]))
        self.assertEqual(response.status_code, 200)

        response = self._patch(reverse(VIEW_NAME, args=[str(self.id)]),
                               data={})
        self.assertEqual(response.status_code, 200)

        response = self._patch(reverse(VIEW_NAME, args=[str(self.id)]),
                               data={"author": "Maximiliane Musterfrau"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.reason_phrase,
                         "The follwoing fields must not be updated: 'author'.")

        response = self._patch(reverse(VIEW_NAME, args=[str(self.id)]),
                               data={"author": "Maximiliane Musterfrau",
                                     "id": "12345"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.reason_phrase,
                         "The follwoing fields must not be updated: 'author'" +
                         ", 'id'.")

        response = self._patch(reverse(VIEW_NAME, args=[str(self.id)]),
                               data={"readonly_users": testuser2.username})
        self.assertEqual(response.status_code, 200)

        obj = DataSet.objects.get(id=self.id)
        self.assertEqual(list(get_objects_for_user(testuser2,
                                                   "view_dataset",
                                                   DataSet)),
                         [obj])

        response = self._patch(reverse(VIEW_NAME, args=[str(self.id)]),
                               data={"readonly_users": "Maxi Musterfrau"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.reason_phrase,
                         "User Maxi Musterfrau does not exist")

        response = self._patch(reverse(VIEW_NAME, args=[str(self.id)]),
                               data={"readonly_users": testuser3.username,
                                     "readwrite_users": testuser2.username})
        self.assertEqual(response.status_code, 200)
        obj = DataSet.objects.get(id=self.id)
        self.assertEqual(list(get_objects_for_user(testuser2,
                                                   "view_dataset",
                                                   DataSet)),
                         [])

        self.assertEqual(list(get_objects_for_user(testuser2,
                                                   "change_dataset",
                                                   DataSet)),
                         [obj])
        self.assertEqual(list(get_objects_for_user(testuser3,
                                                   "view_dataset",
                                                   DataSet)),
                         [obj])
        self.assertEqual(list(get_objects_for_user(testuser3,
                                                   "change_dataset",
                                                   DataSet)),
                         [])

        response = self._patch(reverse(VIEW_NAME, args=[str(self.id)]),
                               data={"readonly_users": [None]})
        self.assertEqual(response.status_code, 200)
        obj = DataSet.objects.get(id=self.id)
        self.assertEqual(list(get_objects_for_user(testuser2,
                                                   "view_dataset",
                                                   DataSet)),
                         [])

        self.assertEqual(list(get_objects_for_user(testuser2,
                                                   "change_dataset",
                                                   DataSet)),
                         [obj])

        response = self._patch(reverse(VIEW_NAME, args=[str(self.id)]),
                               data={"readwrite_users": [None]})
        self.assertEqual(response.status_code, 200)
        obj = DataSet.objects.get(id=self.id)
        self.assertEqual(list(get_objects_for_user(testuser2,
                                                   "view_dataset",
                                                   DataSet)),
                         [])

        self.assertEqual(list(get_objects_for_user(testuser2,
                                                   "change_dataset",
                                                   DataSet)),
                         [])

    def test_dataset_patch_groups(self):
        testgroup1 = Group.objects.create(name="testgroup1")
        testgroup2 = Group.objects.create(name="testgroup2")

        self._create_test_dataset()

        response = self._patch(reverse(VIEW_NAME, args=[str(self.id)]),
                               data={"": "Maximiliane Musterfrau"})

        response = self._patch(reverse(VIEW_NAME, args=[str(self.id)]),
                               data={"readonly_groups": testgroup1.name})
        self.assertEqual(response.status_code, 200)
        obj = DataSet.objects.get(id=self.id)
        self.assertEqual(list(get_objects_for_group(testgroup1,
                                                    "view_dataset",
                                                    DataSet)),
                         [obj])

        response = self._patch(reverse(VIEW_NAME, args=[str(self.id)]),
                               data={"readonly_groups": testgroup2.name,
                                     "readwrite_groups": testgroup1.name})
        self.assertEqual(response.status_code, 200)
        obj = DataSet.objects.get(id=self.id)
        self.assertEqual(list(get_objects_for_group(testgroup1,
                                                    "view_dataset",
                                                    DataSet)),
                         [])

        self.assertEqual(list(get_objects_for_group(testgroup1,
                                                    "change_dataset",
                                                    DataSet)),
                         [obj])
        self.assertEqual(list(get_objects_for_group(testgroup2,
                                                    "view_dataset",
                                                    DataSet)),
                         [obj])
        self.assertEqual(list(get_objects_for_group(testgroup2,
                                                    "change_dataset",
                                                    DataSet)),
                         [])

        response = self._patch(reverse(VIEW_NAME, args=[str(self.id)]),
                               data={"readonly_groups": [None],
                                     "readwrite_groups": [None]})
        self.assertEqual(response.status_code, 200)
        obj = DataSet.objects.get(id=self.id)
        self.assertEqual(list(get_objects_for_group(testgroup1,
                                                    "view_dataset",
                                                    DataSet)), [])

        self.assertEqual(list(get_objects_for_group(testgroup1,
                                                    "change_dataset",
                                                    DataSet)), [])
        self.assertEqual(list(get_objects_for_group(testgroup2,
                                                    "view_dataset",
                                                    DataSet)), [])
        self.assertEqual(list(get_objects_for_group(testgroup2,
                                                    "change_dataset",
                                                    DataSet)), [])

    def test_dataset_patch_valid(self):
        self._create_test_dataset()
        obj = DataSet.objects.get(id=self.id)
        self.assertTrue(obj.valid)

        response = self._patch(reverse(VIEW_NAME, args=[str(self.id)]),
                               data={"valid": True})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(obj.valid)

        response = self._patch(reverse(VIEW_NAME, args=[str(self.id)]),
                               data={"valid": False})
        self.assertEqual(response.status_code, 200)
        obj = DataSet.objects.get(id=self.id)
        self.assertFalse(obj.valid)

        response = self._patch(reverse(VIEW_NAME, args=[str(self.id)]),
                               data={"valid": True})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.reason_phrase,
                         "It is not possible to change the status of a " +
                         "dataset from invalid to valid.")
