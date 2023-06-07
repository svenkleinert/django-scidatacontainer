from django.test import TestCase
from django.contrib.auth.models import User

from datetime import datetime, timezone
import uuid

from scidatacontainer_db.models import ContainerType, DataSet, Keyword,\
                                       Software


class DataSetTest(TestCase):

    def test_version_0_3(self):
        testuser = User.objects.create_user("Testuser")
        dc = DataSet()
        dc.owner = testuser

        now = datetime.now().replace(tzinfo=timezone.utc)
        d = {}

        d["complete"] = False
        d["valid"] = False
        d["size"] = 200

        d["created"] = now
        d["modified"] = now
        d["static"] = False
        ct = ContainerType(name="TestType2", id="TestID", version="1.0")
        ct.save()
        d["container_type"] = ct
        d["hash"] = "jklafljfkhal"
        s1 = Software(name="TestSoftware", version="1.1")
        s1.save()
        s2 = Software(name="TestSoftware2", version="2.0")
        s2.save()
        d["used_software"] = [s1, s2]
        d["model_version"] = "0.3"

        d["author"] = "Max Mustermann"
        d["email"] = "max.mustermann@phoenixd.uni-hannover.de"
        d["comment"] = "TestComment"
        d["title"] = "TestTitle"
        kw1 = Keyword(name="TestKeyword")
        kw1.save()
        kw2 = Keyword(name="TestKeyword2")
        kw2.save()
        d["keywords"] = [kw1, kw2]
        d["description"] = "TestDescription"

        d["content"] = []

        dc.update_attributes(d, testuser)
        dc.save()

        for key, value in d.items():
            fieldtype = DataSet._meta.get_field(key).get_internal_type()

            if fieldtype == "ManyToManyField":
                for item in getattr(dc, key).all():
                    self.assertIn(item, value)
            else:
                self.assertEqual(getattr(dc, key), value)

        return dc, d

    def test_version_0_5(self):
        dc, d = self.test_version_0_3()

        d["timestamp"] = datetime.now().replace(tzinfo=timezone.utc)
        d["doi"] = "testdoi"
        d["license"] = "MIT"
        d["model_version"] = "0.5"

        dc2 = DataSet(id=uuid.uuid4(), owner=dc.owner)
        dc2.update_attributes(d, dc.owner)
        dc2.save()

        for key, value in d.items():
            fieldtype = DataSet._meta.get_field(key).get_internal_type()

            if fieldtype == "ManyToManyField":
                for item in getattr(dc2, key).all():
                    self.assertIn(item, value)
            else:
                self.assertEqual(getattr(dc2, key), value)
