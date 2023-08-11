from django.contrib.auth.models import User, Group

from guardian.shortcuts import assign_perm

from scidatacontainer_db.parsers import parse_container_file
from . import TestCase, get_example_zdc


class DataSetPermissionTest(TestCase):

    def test_dataset_permission(self):
        testuser1 = User.objects.create_user("Testuser1")
        testuser2 = User.objects.create_user("Testuser2")
        testuser3 = User.objects.create_user("Testuser3")

        testgroup1 = Group.objects.create(name="Testgroup1")
        testgroup2 = Group.objects.create(name="Testgroup2")

        file = self._create_temp_from_container(get_example_zdc())
        obj = parse_container_file(file, testuser1)

        self.assertEqual(len(obj.get_read_perm_user_list()), 0)
        self.assertEqual(len(obj.get_write_perm_user_list()), 0)
        self.assertEqual(len(obj.get_read_perm_group_list()), 0)
        self.assertEqual(len(obj.get_write_perm_group_list()), 0)

        assign_perm("view_dataset", testuser2, obj)
        self.assertIn(testuser2, obj.get_read_perm_user_list())
        self.assertEqual(len(obj.get_read_perm_user_list()), 1)
        self.assertEqual(len(obj.get_write_perm_user_list()), 0)
        self.assertEqual(len(obj.get_read_perm_group_list()), 0)
        self.assertEqual(len(obj.get_write_perm_group_list()), 0)

        assign_perm("change_dataset", testuser3, obj)
        self.assertIn(testuser2, obj.get_read_perm_user_list())
        self.assertEqual(len(obj.get_read_perm_user_list()), 1)
        self.assertEqual(len(obj.get_write_perm_user_list()), 1)
        self.assertIn(testuser3, obj.get_write_perm_user_list())
        self.assertEqual(len(obj.get_read_perm_group_list()), 0)
        self.assertEqual(len(obj.get_write_perm_group_list()), 0)

        assign_perm("view_dataset", testgroup1, obj)
        self.assertIn(testuser2, obj.get_read_perm_user_list())
        self.assertEqual(len(obj.get_read_perm_user_list()), 1)
        self.assertEqual(len(obj.get_write_perm_user_list()), 1)
        self.assertIn(testuser3, obj.get_write_perm_user_list())
        self.assertEqual(len(obj.get_read_perm_group_list()), 1)
        self.assertIn(testgroup1, obj.get_read_perm_group_list())
        self.assertEqual(len(obj.get_write_perm_group_list()), 0)

        assign_perm("change_dataset", testgroup2, obj)
        self.assertEqual(len(obj.get_read_perm_user_list()), 1)
        self.assertIn(testuser2, obj.get_read_perm_user_list())
        self.assertEqual(len(obj.get_write_perm_user_list()), 1)
        self.assertIn(testuser3, obj.get_write_perm_user_list())
        self.assertEqual(len(obj.get_read_perm_group_list()), 1)
        self.assertIn(testgroup1, obj.get_read_perm_group_list())
        self.assertEqual(len(obj.get_write_perm_group_list()), 1)
        self.assertIn(testgroup2, obj.get_write_perm_group_list())
