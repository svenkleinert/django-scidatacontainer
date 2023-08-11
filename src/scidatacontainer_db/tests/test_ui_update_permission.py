from django.contrib.auth.models import Group, User
from django.urls import reverse

from scidatacontainer_db.models import DataSet
from . import TestCase


class UpdatePermissionTest(TestCase):

    def test_view_url_exists_at_desired_location(self):
        self._create_test_dataset()
        response = self._get("/" + str(self.id) + "/permissions/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        self._create_test_dataset()
        response = self._get(self.perm_url)
        self.assertEqual(response.status_code, 200)

    def test_template(self):
        self._create_test_dataset()
        response = self._get(self.perm_url)
        self.assertTemplateUsed(response,
                                "scidatacontainer_db/update_permissions.html")

    def test_create_permission(self):
        self._create_test_dataset()
        testuser2 = User.objects.create_user("testuser2")
        testuser3 = User.objects.create_user("testuser3")

        testgroup1 = Group.objects.create(name="testgroup1")
        testgroup2 = Group.objects.create(name="testgroup2")

        dataset = DataSet.objects.get(id=self.id)
        self.assertEqual(len(dataset.get_read_perm_user_list()), 0)
        self.assertEqual(len(dataset.get_write_perm_user_list()), 0)
        self.assertEqual(len(dataset.get_read_perm_group_list()), 0)
        self.assertEqual(len(dataset.get_write_perm_group_list()), 0)

        response = self._post(self.perm_url,
                              data={"owner": "",
                                    "newuser": testuser2.username,
                                    "newuser_rw-outlined": "ro",
                                    "newgroup": "",
                                    }
                              )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(dataset.get_read_perm_user_list()), 1)
        self.assertIn(testuser2, dataset.get_read_perm_user_list())
        self.assertEqual(len(dataset.get_write_perm_user_list()), 0)
        self.assertEqual(len(dataset.get_read_perm_group_list()), 0)
        self.assertEqual(len(dataset.get_write_perm_group_list()), 0)

        response = self._post(self.perm_url,
                              data={"owner": "",
                                    "newuser": testuser3.username,
                                    "newuser_rw-outlined": "rw",
                                    "newgroup": testgroup1.name,
                                    "newgroup_rw-outlined": "ro",
                                    })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(dataset.get_read_perm_user_list()), 1)
        self.assertIn(testuser2, dataset.get_read_perm_user_list())
        self.assertEqual(len(dataset.get_write_perm_user_list()), 1)
        self.assertIn(testuser3, dataset.get_write_perm_user_list())
        self.assertEqual(len(dataset.get_read_perm_group_list()), 1)
        self.assertIn(testgroup1, dataset.get_read_perm_group_list())
        self.assertEqual(len(dataset.get_write_perm_group_list()), 0)

        response = self._post(self.perm_url,
                              data={"owner": "",
                                    "newuser": "",
                                    "newgroup": testgroup2.name,
                                    "newgroup_rw-outlined": "rw",
                                    })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(dataset.get_read_perm_user_list()), 1)
        self.assertIn(testuser2, dataset.get_read_perm_user_list())
        self.assertEqual(len(dataset.get_write_perm_user_list()), 1)
        self.assertIn(testuser3, dataset.get_write_perm_user_list())
        self.assertEqual(len(dataset.get_read_perm_group_list()), 1)
        self.assertIn(testgroup1, dataset.get_read_perm_group_list())
        self.assertEqual(len(dataset.get_write_perm_group_list()), 1)
        self.assertIn(testgroup2, dataset.get_write_perm_group_list())

        response = self._post(self.perm_url,
                              data={"owner": "",
                                    "newuser": "testuser4",
                                    "newgroup": "",
                                    "newgroup_rw-outlined": "rw",
                                    })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(dataset.get_read_perm_user_list()), 1)
        self.assertIn(testuser2, dataset.get_read_perm_user_list())
        self.assertEqual(len(dataset.get_write_perm_user_list()), 1)
        self.assertIn(testuser3, dataset.get_write_perm_user_list())
        self.assertEqual(len(dataset.get_read_perm_group_list()), 1)
        self.assertIn(testgroup1, dataset.get_read_perm_group_list())
        self.assertEqual(len(dataset.get_write_perm_group_list()), 1)
        self.assertIn(testgroup2, dataset.get_write_perm_group_list())

        msgs = [str(m) for m in list(response.wsgi_request._messages)]
        self.assertEqual(len(msgs), 1)
        self.assertIn("User \"testuser4\" does not exist!", msgs)

        response = self._post(self.perm_url,
                              data={"owner": "",
                                    "newuser": "",
                                    "newgroup": "testgroup3",
                                    })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(dataset.get_read_perm_user_list()), 1)
        self.assertIn(testuser2, dataset.get_read_perm_user_list())
        self.assertEqual(len(dataset.get_write_perm_user_list()), 1)
        self.assertIn(testuser3, dataset.get_write_perm_user_list())
        self.assertEqual(len(dataset.get_read_perm_group_list()), 1)
        self.assertIn(testgroup1, dataset.get_read_perm_group_list())
        self.assertEqual(len(dataset.get_write_perm_group_list()), 1)
        self.assertIn(testgroup2, dataset.get_write_perm_group_list())

        msgs = [str(m) for m in list(response.wsgi_request._messages)]
        self.assertEqual(len(msgs), 2)
        self.assertIn("Group \"testgroup3\" does not exist!", msgs)

    def test_update_permission(self):
        self.test_create_permission()

        testuser2 = User.objects.get(username="testuser2")
        testuser3 = User.objects.get(username="testuser3")
        testgroup1 = Group.objects.get(name="testgroup1")
        testgroup2 = Group.objects.get(name="testgroup2")
        dataset = DataSet.objects.get(id=self.id)

        response = self._post(self.perm_url,
                              data={"owner": "",
                                    "newuser": "",
                                    "newgroup": "",
                                    "urw_" + str(testuser2.id): "rw"
                                    })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(dataset.get_read_perm_user_list()), 0)
        self.assertNotIn(testuser2, dataset.get_read_perm_user_list())
        self.assertEqual(len(dataset.get_write_perm_user_list()), 2)
        self.assertIn(testuser2, dataset.get_write_perm_user_list())
        self.assertIn(testuser3, dataset.get_write_perm_user_list())
        self.assertEqual(len(dataset.get_read_perm_group_list()), 1)
        self.assertIn(testgroup1, dataset.get_read_perm_group_list())
        self.assertEqual(len(dataset.get_write_perm_group_list()), 1)
        self.assertIn(testgroup2, dataset.get_write_perm_group_list())

        response = self._post(self.perm_url,
                              data={"owner": "",
                                    "newuser": "",
                                    "newgroup": "",
                                    "urw_" + str(testuser3.id): "ro",
                                    "grw_" + testgroup1.name: "rw"
                                    })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(dataset.get_read_perm_user_list()), 1)
        self.assertNotIn(testuser2, dataset.get_read_perm_user_list())
        self.assertIn(testuser3, dataset.get_read_perm_user_list())
        self.assertEqual(len(dataset.get_write_perm_user_list()), 1)
        self.assertIn(testuser2, dataset.get_write_perm_user_list())
        self.assertNotIn(testuser3, dataset.get_write_perm_user_list())
        self.assertEqual(len(dataset.get_read_perm_group_list()), 0)
        self.assertNotIn(testgroup1, dataset.get_read_perm_group_list())
        self.assertEqual(len(dataset.get_write_perm_group_list()), 2)
        self.assertIn(testgroup1, dataset.get_write_perm_group_list())
        self.assertIn(testgroup2, dataset.get_write_perm_group_list())

        response = self._post(self.perm_url,
                              data={"owner": "",
                                    "newuser": "",
                                    "newgroup": "",
                                    "grw_" + testgroup2.name: "ro"
                                    })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(dataset.get_read_perm_user_list()), 1)
        self.assertNotIn(testuser2, dataset.get_read_perm_user_list())
        self.assertIn(testuser3, dataset.get_read_perm_user_list())
        self.assertEqual(len(dataset.get_write_perm_user_list()), 1)
        self.assertIn(testuser2, dataset.get_write_perm_user_list())
        self.assertNotIn(testuser3, dataset.get_write_perm_user_list())
        self.assertEqual(len(dataset.get_read_perm_group_list()), 1)
        self.assertNotIn(testgroup1, dataset.get_read_perm_group_list())
        self.assertIn(testgroup2, dataset.get_read_perm_group_list())
        self.assertEqual(len(dataset.get_write_perm_group_list()), 1)
        self.assertIn(testgroup1, dataset.get_write_perm_group_list())
        self.assertNotIn(testgroup2, dataset.get_write_perm_group_list())

    def test_delete_permission(self):
        self.test_create_permission()

        testuser2 = User.objects.get(username="testuser2")
        testuser3 = User.objects.get(username="testuser3")
        testgroup1 = Group.objects.get(name="testgroup1")
        testgroup2 = Group.objects.get(name="testgroup2")
        dataset = DataSet.objects.get(id=self.id)

        response = self._post(self.perm_url,
                              data={"owner": "",
                                    "newuser": "",
                                    "newgroup": "",
                                    "delete-user": testuser2.id,
                                    })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(dataset.get_read_perm_user_list()), 0)
        self.assertNotIn(testuser2, dataset.get_read_perm_user_list())
        self.assertEqual(len(dataset.get_write_perm_user_list()), 1)
        self.assertIn(testuser3, dataset.get_write_perm_user_list())
        self.assertEqual(len(dataset.get_read_perm_group_list()), 1)
        self.assertIn(testgroup1, dataset.get_read_perm_group_list())
        self.assertEqual(len(dataset.get_write_perm_group_list()), 1)
        self.assertIn(testgroup2, dataset.get_write_perm_group_list())

        response = self._post(self.perm_url,
                              data={"owner": "",
                                    "newuser": "",
                                    "newgroup": "",
                                    "delete-group": testgroup1.name,
                                    })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(dataset.get_read_perm_user_list()), 0)
        self.assertNotIn(testuser2, dataset.get_read_perm_user_list())
        self.assertEqual(len(dataset.get_write_perm_user_list()), 1)
        self.assertIn(testuser3, dataset.get_write_perm_user_list())
        self.assertEqual(len(dataset.get_read_perm_group_list()), 0)
        self.assertNotIn(testgroup1, dataset.get_read_perm_group_list())
        self.assertEqual(len(dataset.get_write_perm_group_list()), 1)
        self.assertIn(testgroup2, dataset.get_write_perm_group_list())

        response = self._post(self.perm_url,
                              data={"owner": "",
                                    "newuser": testuser2.username,
                                    "newuser_rw-outlined": "ro",
                                    "newgroup": "",
                                    "urw_" + str(testuser3.id): "ro",
                                    "delete-group": testgroup2.name,
                                    })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(dataset.get_read_perm_user_list()), 2)
        self.assertIn(testuser2, dataset.get_read_perm_user_list())
        self.assertIn(testuser3, dataset.get_read_perm_user_list())
        self.assertEqual(len(dataset.get_write_perm_user_list()), 0)
        self.assertEqual(len(dataset.get_read_perm_group_list()), 0)
        self.assertEqual(len(dataset.get_write_perm_group_list()), 0)

    def test_change_owner(self):
        self._create_test_dataset()
        testuser2 = User.objects.create_user("testuser2")
        dataset = DataSet.objects.get(id=self.id)
        self.assertEqual(dataset.owner, self.user)

        response = self._post(self.perm_url,
                              data={"owner": testuser2.username,
                                    "newuser": "",
                                    "newgroup": "",
                                    })
        self.assertRedirects(response, reverse("scidatacontainer_db:ui-index"))
        dataset = DataSet.objects.get(id=self.id)
        self.assertEqual(dataset.owner, testuser2)

        dataset.owner = self.user
        dataset.save()
        response = self._post(self.perm_url,
                              data={"owner": "",
                                    "newuser": self.user.username,
                                    "newuser_rw-outlined": "ro",
                                    "newgroup": "",
                                    })

        response = self._post(self.perm_url,
                              data={"owner": testuser2.username,
                                    "newuser": "",
                                    "newgroup": "",
                                    })
        self.assertRedirects(response, reverse("scidatacontainer_db:ui-detail",
                                               args=[str(self.id)]))
        dataset = DataSet.objects.get(id=self.id)
        self.assertEqual(dataset.owner, testuser2)

        response = self._post(self.perm_url,
                              data={"owner": testuser2.username,
                                    "newuser": "",
                                    "newgroup": "",
                                    })
        self.assertEqual(response.status_code, 403)
        dataset = DataSet.objects.get(id=self.id)
        self.assertEqual(dataset.owner, testuser2)

        dataset.owner = self.user
        dataset.save()
        response = self._post(self.perm_url,
                              data={"owner": "testuser3",
                                    "newuser": "",
                                    "newgroup": "",
                                    })
        self.assertRedirects(response, self.perm_url)
        self.assertEqual(dataset.owner, self.user)
        msgs = [str(m) for m in list(response.wsgi_request._messages)]
        self.assertEqual(len(msgs), 1)
        self.assertIn("User \"testuser3\" does not exist!", msgs)
