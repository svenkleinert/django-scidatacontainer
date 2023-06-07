from django.test import TestCase
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth.models import User

from datetime import datetime, timezone, timedelta
import mimetypes
import uuid

from scidatacontainer_db.models import ContainerType, DataSet, Keyword,\
                                       Software, DataSetBase
from scidatacontainer_db.parsers import parse_container_file
from scidatacontainer_db.utils import MetaDBError
from . import TESTDIR


class DataSetTest(TestCase):

    def test_dataset_creation(self):
        testuser = User.objects.create_user("Testuser")

        container_type = ContainerType.to_ContainerType({"name": "TestType"})

        now = datetime.now().replace(tzinfo=timezone.utc)
        d = DataSet(complete=True,
                    valid=True,
                    size=20000,
                    created=now,
                    modified=now,
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
        self.assertEqual(d.modified, now)
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
        d["modified"] = d["modified"] - timedelta(seconds=1)

        with self.assertRaisesMessage(MetaDBError,
                                      "{'error_code': 400, 'msg': 'Server " +
                                      "version of the dataset is newer than " +
                                      "the file you tried to upload.'}"):
            dc.update_attributes(d, dc.owner)

        d["modified"] = d["modified"] + timedelta(seconds=2)

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

    def _create_temp_from_file(self, filename):
        file_object = open(filename, "rb")

        def getsize(f):
            f.seek(0)
            f.read()
            s = f.tell()
            f.seek(0)
            return s

        name = filename.split('/')[-1]
        content_type, charset = mimetypes.guess_type(name)
        size = getsize(file_object)

        file = InMemoryUploadedFile(file=file_object, name=name,
                                    field_name=None, content_type=content_type,
                                    charset=charset, size=size)
        return file

    def test_dataset_parse_zip_file(self):
        testuser = User.objects.create_user("Testuser")

        file = self._create_temp_from_file(TESTDIR + "example.zdc")
        obj = parse_container_file(file, testuser)
        obj.save()
        timestamp = datetime(2023, 2, 21,
                             9, 47, 31).replace(tzinfo=timezone.utc)
        self.assertEqual(obj.complete, False)
        self.assertEqual(obj.container_type.name, "myImage")
        self.assertEqual(obj.created, timestamp)
        self.assertEqual(obj.hash, "389c050aadb9ea13c488975c035f06ae3b46c92" +
                                   "b89e69d09a3414958f7521ff9")
        self.assertEqual(obj.model_version, "0.3.1")
        self.assertEqual(obj.modified, timestamp)
        self.assertEqual(obj.replaces, None)
        self.assertEqual(obj.static, False)
        self.assertEqual(len(obj.used_software.all()), 2)
        self.assertEqual(obj.id, "a31cb576-494f-40c9-af95-e756271278c3")

        self.assertEqual(obj.author, "Reinhard Caspary")
        self.assertEqual(obj.comment, "")
        self.assertEqual(obj.description, "")
        self.assertEqual(obj.email,
                         "reinhard.caspary@phoenixd.uni-hannover.de")
        self.assertEqual(len(obj.keywords.all()), 2)
        self.assertEqual(obj.title, "This is a sample image dataset")

        # updating dataset
        file = self._create_temp_from_file(TESTDIR + "example_update.zdc")
        obj = parse_container_file(file, testuser)
        obj.save()
        self.assertEqual(obj.container_type.name, "myImage2")
        self.assertEqual(obj.modified, timestamp + timedelta(seconds=6))
        lib1 = obj.used_software.get(name="TestLibrary")
        lib2 = obj.used_software.get(name="TestLib2")
        self.assertEqual(lib1.version, "0.2")
        self.assertEqual(lib2.version, "1.2")

        id = obj.id
        obj.delete()
        obj = DataSetBase(id=id)
        obj.save()
        self.assertFalse(isinstance(obj, DataSet))
        self.assertTrue(isinstance(obj, DataSetBase))

        obj = parse_container_file(file, testuser)
        obj.save()
        self.assertTrue(isinstance(obj, DataSet))
        obj.delete()

        # invalid datasets
        file = self._create_temp_from_file(TESTDIR + "example_wo_complete.zdc")

        with self.assertRaisesMessage(MetaDBError,
                                      "{'error_code': 400, 'msg': \""
                                      "Attribute 'complete' required in " +
                                      "content.json.\"}"):
            obj = parse_container_file(file, testuser)

        file = self._create_temp_from_file(TESTDIR + "example_wo_author.zdc")

        with self.assertRaisesMessage(MetaDBError,
                                      "{'error_code': 400, 'msg': \"" +
                                      "Attribute 'author' required in" +
                                      " meta.json.\"}"):
            obj = parse_container_file(file, testuser)

        file = self._create_temp_from_file(TESTDIR + "example_faulty_id.zdc")
        with self.assertRaisesMessage(MetaDBError,
                                      "{'error_code': 400, 'msg': \"" +
                                      "ValidationError: ['“" +
                                      "a31cb576-494f-40c9-af95” is not a " +
                                      "valid UUID.']\"}"):
            obj = parse_container_file(file, testuser)

        file = self._create_temp_from_file(TESTDIR + "example_version.zdc")
        with self.assertRaisesMessage(MetaDBError,
                                      "{'error_code': 400, 'msg': 'You tried" +
                                      " to upload a dataset complying " +
                                      "scidatacontainer model version 0.2.19" +
                                      " but the server requires a minimum " +
                                      "model version of 0.3'}"):
            obj = parse_container_file(file, testuser)

    def test_dataset_parse_hdf5_file(self):
        pass

    def test_dataset_parse_pxd_file(self):
        testuser = User.objects.create_user("Testuser")

        file = self._create_temp_from_file(TESTDIR + "test_file.py")
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

        file = self._create_temp_from_file(TESTDIR + "example_replaces.zdc")
        obj = parse_container_file(file, dc.owner)
        obj.save()
        self.assertTrue(isinstance(obj.replaces, DataSetBase))
        self.assertFalse(isinstance(obj.replaces, DataSet))

        file = self._create_temp_from_file(TESTDIR + "example_faulty.zdc")
        with self.assertRaisesMessage(MetaDBError,
                                      "{'error_code': 400, 'msg': \"Failed " +
                                      "to convert '2023-02-21 UTC' using the" +
                                      " default parser. Make sure it has the" +
                                      " right type.\"}"):
            obj = parse_container_file(file, dc.owner)
