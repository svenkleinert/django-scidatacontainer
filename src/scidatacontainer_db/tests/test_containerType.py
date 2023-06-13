from django.test import TestCase
from scidatacontainer_db.models import ContainerType


class ContainerTypeTest(TestCase):

    def test_containerType_creation(self):
        c = ContainerType(name="TestType")
        c.save()
        self.assertTrue(isinstance(c, ContainerType))
        self.assertEqual(c.name, "TestType")
        self.assertEqual(str(c), "TestType")

        c = ContainerType(name="TestType2",
                          id="testID",
                          version="0.1")
        c.save()
        self.assertTrue(isinstance(c, ContainerType))
        self.assertEqual(c.name, "TestType2")
        self.assertEqual(c.id, "testID")
        self.assertEqual(c.version, "0.1")
        self.assertEqual(str(c), "TestType2, v0.1")

    def test_containerType_creation_from_dict(self):
        c = ContainerType.to_ContainerType("TestType3")
        c.save()
        self.assertTrue(isinstance(c, ContainerType))
        self.assertEqual(c.name, "TestType3")

        c = ContainerType.to_ContainerType({"name": "TestType4",
                                            "id": "testID2",
                                            "version": "0.2"})
        c.save()
        self.assertTrue(isinstance(c, ContainerType))
        self.assertEqual(c.name, "TestType4")
        self.assertEqual(c.id, "testID2")
        self.assertEqual(c.version, "0.2")

        rejected = False
        try:
            c = ContainerType.to_ContainerType([{"id": "testID2",
                                                "version": "0.2"}])
        except AssertionError as e:
            rejected = True
            self.assertEqual(str(e),
                             "ContainerType needs to be a " +
                             "string (name) or a dictionary.")
        self.assertTrue(rejected)

        rejected = False
        try:
            c = ContainerType.to_ContainerType({"id": "testID2",
                                                "version": "0.2"})
        except AssertionError as e:
            rejected = True
            self.assertEqual(str(e),
                             "ContainerType requires name attribute.")
        self.assertTrue(rejected)

        rejected = False
        try:
            c = ContainerType.to_ContainerType({"name": "TestType4",
                                                "id": "testID2"})
        except AssertionError as e:
            rejected = True
            self.assertEqual(str(e),
                             "ContainerType requires version" +
                             "attribute if id is given")
        self.assertTrue(rejected)
