from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth.models import User

from datetime import date, datetime, timezone, timedelta
import mimetypes
import io
import uuid

from scidatacontainer_db.models import ContainerType, DataSet, Keyword,\
                                       Software, DataSetBase
from scidatacontainer_db.parsers import parse_container_file
from scidatacontainer_db.utils import MetaDBError
from . import get_example_zdc,\
              get_example_faulty_zdc,\
              get_example_faulty_id_zdc,\
              get_example_replaces_zdc,\
              get_example_update_zdc,\
              get_example_version_zdc,\
              get_example_wo_complete_zdc,\
              get_example_wo_author_zdc,\
              testuuid,\
              TestCase


class DataSetTest(TestCase):

    def test_dataset_creation(self):
        testuser = User.objects.create_user("Testuser")

        container_type = ContainerType.to_ContainerType({"name": "TestType"})

        now = datetime.now().replace(tzinfo=timezone.utc)
        d = DataSet(complete=True,
                    valid=True,
                    size=20000,
                    created=now,
                    storage_time=now,
                    static=False,
                    owner=testuser,
                    container_type=container_type,
                    )
        d.save()

        self.assertTrue(isinstance(d, DataSet))
        self.assertGreater(d.upload_time, now)
        self.assertEqual(d.complete, True)
        self.assertEqual(d.valid, True)
        self.assertEqual(d.size, 20000)
        self.assertEqual(d.created, now)
        self.assertEqual(d.storage_time, now)
        self.assertEqual(d.static, False)
        self.assertEqual(d.owner, testuser)
        self.assertEqual(d.container_type.name, container_type.name)

    def create_dataset(self):
        testuser = User.objects.create_user("Testuser")

        dc = DataSet()
        dc.owner = testuser

        now = datetime.now().replace(tzinfo=timezone.utc)
        d = {}

        d["complete"] = False
        d["valid"] = False
        d["size"] = 200

        d["created"] = now
        d["storage_time"] = now
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
        d["model_version"] = "1.0.0"

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
        return dc, d

    def test_dataset_update(self):
        dc, d = self.create_dataset()
        for key, value in d.items():
            fieldtype = DataSet._meta.get_field(key).get_internal_type()

            if fieldtype == "ManyToManyField":
                for item in getattr(dc, key).all():
                    self.assertIn(item, value)
            else:
                self.assertEqual(getattr(dc, key), value)

        testuser2 = User.objects.create_user("Testuser2")
        with self.assertRaisesMessage(MetaDBError,
                                      "{'error_code': 403, 'msg': \"You " +
                                      "don't have permission to update this " +
                                      "dataset.\"}"):
            dc.update_attributes(d, testuser2)

        dc.complete = True
        dc.save()
        with self.assertRaisesMessage(MetaDBError,
                                      "{'error_code': 409, 'msg': 'Dataset " +
                                      "is marked complete. No further " +
                                      "changes allowed.'}"):
            dc.update_attributes(d, dc.owner)

        dc.complete = False
        d["static"] = True
        del d["hash"]
        with self.assertRaisesMessage(MetaDBError,
                                      "{'error_code': 400, 'msg': 'A static " +
                                      "dataset requires the hash attribute.'}"
                                      ):
            dc.update_attributes(d, dc.owner)

        d["hash"] = "jklafljfkhal"
        dc.hash = "jklafljfkhal"
        dc.static = True
        dc.save()
        with self.assertRaisesMessage(MetaDBError,
                                      "{'error_code': 301, 'msg': 'A static " +
                                      "file requires a unique hash, but " +
                                      "there is already a file with the " +
                                      "same hash and UUID=" + str(dc.id) +
                                      ".', 'object': <DataSet: " +
                                      "DataSet object (" + str(dc.id) + ")>}"):
            dc.update_attributes(d, dc.owner)

        d["static"] = False
        d["storage_time"] -= timedelta(seconds=1)

        with self.assertRaisesMessage(MetaDBError,
                                      "{'error_code': 400, 'msg': 'Server " +
                                      "version of the dataset is newer than " +
                                      "the file you tried to upload.'}"):
            dc.update_attributes(d, dc.owner)

        d["storage_time"] = d["storage_time"] + timedelta(seconds=2)

        dc2 = DataSet()
        dc2.owner = dc.owner
        d["replaces"] = dc
        dc2.update_attributes(d, dc.owner)
        dc2.save()

        self.assertNotEqual(dc2.replaces, None)
        self.assertEqual(dc2.replaces.id, dc.id)
        self.assertEqual(dc.valid, False)
        self.assertTrue(dc.is_replaced)
        self.assertEqual(dc.replaced_by, dc2)

    def test_dataset_parse_zip_file(self):
        testuser = User.objects.create_user("Testuser")

        container = get_example_zdc()
        container.hash()
        file = self._create_temp_from_container(container)
        obj = parse_container_file(file, testuser)
        obj.save()

        t = datetime.fromisoformat(container["content.json"]["created"])
        self.assertEqual(obj.id, container["content.json"]["uuid"])
        self.assertEqual(obj.id, container["content.json"]["uuid"])
        self.assertEqual(obj.replaces.id,
                         container["content.json"]["replaces"])
        self.assertEqual(obj.container_type.name,
                         container["content.json"]["containerType"]["name"])
        self.assertEqual(obj.container_type.id,
                         container["content.json"]["containerType"]["id"])
        self.assertEqual(obj.container_type.version,
                         container["content.json"]["containerType"]["version"])
        self.assertEqual(obj.created, t)
        self.assertEqual(obj.storage_time, t)
        self.assertEqual(obj.static, container["content.json"]["static"])
        self.assertEqual(obj.complete, container["content.json"]["complete"])
        self.assertEqual(obj.hash, container["content.json"]["hash"])
        self.assertEqual(len(obj.used_software.all()),
                         len(container["content.json"]["usedSoftware"]))
        for software in container["content.json"]["usedSoftware"]:
            s_obj = obj.used_software.get(name=software["name"])
            self.assertEqual(s_obj.version, software["version"])
            if "id" in software:
                self.assertEqual(s_obj.id, software["id"])
                self.assertEqual(s_obj.id_type, software["idType"])

        self.assertEqual(obj.model_version,
                         container["content.json"]["modelVersion"])

        self.assertEqual(obj.author, container["meta.json"]["author"])
        self.assertEqual(obj.email,
                         container["meta.json"]["email"])
        self.assertEqual(obj.organization,
                         container["meta.json"]["organization"])
        self.assertEqual(obj.comment, container["meta.json"]["comment"])
        self.assertEqual(obj.title, container["meta.json"]["title"])
        self.assertEqual(len(obj.keywords.all()),
                         len(container["meta.json"]["keywords"]))
        for keyword in container["meta.json"]["keywords"]:
            obj.keywords.get(name=keyword)
        self.assertEqual(obj.title, container["meta.json"]["title"])
        self.assertEqual(obj.description,
                         container["meta.json"]["description"])
        self.assertEqual(obj.timestamp, t)
        self.assertEqual(obj.doi,
                         container["meta.json"]["doi"])
        self.assertEqual(obj.license,
                         container["meta.json"]["license"])

        # updating dataset
        container2 = get_example_update_zdc()
        file = self._create_temp_from_container(container2)
        obj = parse_container_file(file, testuser)
        obj.save()
        self.assertEqual(obj.container_type.name,
                         container2["content.json"]["containerType"]["name"])
        self.assertEqual(obj.storage_time, t + timedelta(seconds=1))

        id = obj.id
        obj.replaces.delete()
        obj.delete()
        obj = DataSetBase(id=id)
        obj.save()
        self.assertFalse(isinstance(obj, DataSet))
        self.assertTrue(isinstance(obj, DataSetBase))

        obj = parse_container_file(file, testuser)
        obj.save()
        self.assertTrue(isinstance(obj, DataSet))
        obj.replaces.delete()
        obj.delete()

        # invalid datasets
        file = self._create_temp_from_container(get_example_wo_complete_zdc())

        with self.assertRaisesMessage(MetaDBError,
                                      "{'error_code': 400, 'msg': \""
                                      "'complete' is a required property in " +
                                      "content.json.\"}"):
            obj = parse_container_file(file, testuser)

        file = self._create_temp_from_container(get_example_wo_author_zdc())

        with self.assertRaisesMessage(MetaDBError,
                                      "{'error_code': 400, 'msg': \"" +
                                      "'author' is a required property in" +
                                      " meta.json.\"}"):
            obj = parse_container_file(file, testuser)

        file = self._create_temp_from_container(get_example_faulty_id_zdc())
        with self.assertRaisesMessage(MetaDBError,
                                      "{'error_code': 400, 'msg': \"Value of" +
                                      " \'uuid\' in content.json has the " +
                                      "wrong format: '" + testuuid[:-4] + "'" +
                                      " is not a 'uuid'.\"}"):
            obj = parse_container_file(file, testuser)

        file = self._create_temp_from_container(get_example_version_zdc())
        with self.assertRaisesMessage(MetaDBError,
                                      "{'error_code': 400, 'msg': 'You tried" +
                                      " to upload a dataset complying " +
                                      "scidatacontainer model version 0.2" +
                                      " but the server requires a minimum " +
                                      "model version of 1.0.0'}"):
            obj = parse_container_file(file, testuser)

    def test_dataset_parse_hdf5_file(self):
        pass

    def test_dataset_parse_pxd_file(self):
        testuser = User.objects.create_user("Testuser")

        def getsize(f):
            f.seek(0)
            f.read()
            s = f.tell()
            f.seek(0)
            return s

        name = "test.py"
        content = io.BytesIO(b'import numpy as np\nprint("Test")')
        content_type, charset = mimetypes.guess_type(name)
        size = getsize(content)

        file = InMemoryUploadedFile(file=content, name=name,
                                    field_name=None, content_type=content_type,
                                    charset=charset, size=size)
        with self.assertRaisesMessage(MetaDBError,
                                      "{'error_code': 415, 'msg': 'File " +
                                      "format has to be hdf5 or zip!'}"):
            parse_container_file(file, testuser)

    def test_replaced(self):
        dc, d = self.create_dataset()
        d["replaces"] = dc

        dc2 = DataSet(id=uuid.uuid4())
        dc2.owner = dc.owner
        dc2.update_attributes(d, dc.owner)
        dc2.save()

        self.assertTrue(dc.is_replaced)
        self.assertFalse(dc2.is_replaced)
        self.assertEqual(dc.replaces, None)
        self.assertEqual(dc.replaced_by, dc2)
        self.assertEqual(dc2.replaces, dc)
        self.assertEqual(dc2.replaced_by, None)
        self.assertTrue(isinstance(dc.replaced_by, DataSet))
        self.assertTrue(isinstance(dc2.replaces, DataSet))

        dc3 = DataSet(id=uuid.uuid4())
        dc3.owner = dc.owner
        with self.assertRaisesMessage(MetaDBError,
                                      "{'error_code': 409, 'msg': 'Failed to" +
                                      " insert replacement relationship. The" +
                                      " object UUID=" + str(dc.id) + " is " +
                                      "already replaced by " +
                                      "UUID=" + str(dc2.id) + ". You might " +
                                      "want to replace this dataset.', " +
                                      "'object': <DataSet: DataSet object (" +
                                      str(dc2.id) + ")>}"):
            dc3.update_attributes(d, dc.owner)

        dc3 = DataSetBase(id=uuid.uuid4())
        d["replaces"] = dc3
        dc4 = DataSet(id=uuid.uuid4())
        dc4.owner = dc.owner
        dc4.update_attributes(d, dc.owner)

        self.assertTrue(dc3.is_replaced)
        self.assertFalse(dc4.is_replaced)
        self.assertEqual(dc3.replaces, None)
        self.assertEqual(dc3.replaced_by, dc4)
        self.assertEqual(dc4.replaces, dc3)
        self.assertEqual(dc4.replaced_by, None)
        self.assertTrue(isinstance(dc3.replaced_by, DataSet))
        self.assertTrue(isinstance(dc4.replaces, DataSetBase))
        self.assertFalse(isinstance(dc4.replaces, DataSet))

        file = self._create_temp_from_container(get_example_replaces_zdc())
        obj = parse_container_file(file, dc.owner)
        obj.save()
        self.assertTrue(isinstance(obj.replaces, DataSetBase))
        self.assertFalse(isinstance(obj.replaces, DataSet))

        file = self._create_temp_from_container(get_example_faulty_zdc())
        today = date.today()
        with self.assertRaisesMessage(MetaDBError,
                                      "{'error_code': 400, 'msg': \"" +
                                      "Value of \'storageTime\' in " +
                                      "content.json has the wrong format: '" +
                                      str(today) + "' is not a 'date-time'.\"}"
                                      ):
            obj = parse_container_file(file, dc.owner)
