from django.test import TestCase
from scidatacontainer_db.models import Software


class SoftwareTest(TestCase):

    def test_software_creation(self):
        s = Software(name="TestLibrary", version="1.0")
        s.save()
        self.assertTrue(isinstance(s, Software))
        self.assertEqual(s.name, "TestLibrary")
        self.assertEqual(s.version, "1.0")
        self.assertEqual(s.id, "")
        self.assertEqual(s.id_type, "")

    def test_software_creation_from_dict(self):
        s = Software.to_Software({
                                  "name": "TestLibrary",
                                  "version": "1.0",
                                  "id": "numpy",
                                  "idType": "github",
                                 })
        s.save()
        self.assertTrue(isinstance(s, Software))
        self.assertEqual(s.name, "TestLibrary")
        self.assertEqual(s.version, "1.0")
        self.assertEqual(s.id, "numpy")
        self.assertEqual(s.id_type, "github")

        s = Software.to_Software({
                                  "name": "TestLibrary",
                                  "version": "1.0",
                                 })
        s.save()
        self.assertTrue(isinstance(s, Software))
        self.assertEqual(s.name, "TestLibrary")
        self.assertEqual(s.version, "1.0")
        self.assertEqual(s.id, "")
        self.assertEqual(s.id_type, "")

        with self.assertRaisesMessage(AssertionError, "usedSoftware requires" +
                                                      " version attribute."):
            s = Software.to_Software({
                                      "name": "TestLibrary",
                                     })
            s.save()

        with self.assertRaisesMessage(AssertionError, "usedSoftware requires" +
                                                      " name attribute."):
            s = Software.to_Software({
                                      "version": "1.0",
                                     })
            s.save()

        with self.assertRaisesMessage(AssertionError,
                                      "usedSoftware requires" +
                                      " idType if id is given"):
            s = Software.to_Software({
                                      "name": "TestLibrary",
                                      "version": "1.0",
                                      "id": "numpy",
                                     })
            s.save()
