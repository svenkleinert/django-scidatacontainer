from django.test import TestCase
from scidatacontainer_db.models import Keyword


class KeywordTest(TestCase):

    def create_keyword(self, name="Keyword Name"):
        return Keyword(name=name)

    def test_keyword_creation(self):
        kw = self.create_keyword()
        kw.save()
        self.assertTrue(isinstance(kw, Keyword))
        self.assertEqual(str(kw), "Keyword Name")

        kw2 = self.create_keyword("Testname")
        kw2.save()
        self.assertTrue(isinstance(kw2, Keyword))
        self.assertEqual(str(kw2), "Testname")
        self.assertNotEqual(kw2.id, kw.id)
