from django.urls import reverse

from scidatacontainer_db.models import DataSet

import io
import tempfile
import uuid

import h5py

from . import APITestCase, testuuid,\
              get_example_zdc,\
              get_example_update_zdc,\
              get_example_wo_author_zdc,\
              get_example_static_zdc,\
              get_example_static_wo_hash_zdc,\
              get_example_static_wrong_hash_zdc


class ApiUploadTest(APITestCase):
    view_name = "scidatacontainer_db:api:dataset-list"

    def test_view_url_exists_at_desired_location(self):
        response = self._post("/api/datasets/")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.reason_phrase,
                         "No data file found in your request!")

    def test_view_url_accessible_by_name(self):
        response = self._post(reverse(self.view_name))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.reason_phrase,
                         "No data file found in your request!")

    def test_http_method(self):
        response = self._post(reverse(self.view_name))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.reason_phrase,
                         "No data file found in your request!")

    def test_upload(self):
        self.assertEqual(len(DataSet.objects.filter(id=testuuid)), 0)
        response = self._post(reverse(self.view_name),
                              data={"uploadfile":
                                    io.BytesIO(get_example_zdc().encode())}
                              )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(DataSet.objects.filter(id=testuuid)), 1)

        b = get_example_wo_author_zdc().encode()
        response = self._post(reverse(self.view_name),
                              data={"uploadfile":
                                    io.BytesIO(b)
                                    }
                              )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.reason_phrase,
                         "'author' is a required property in meta.json.")

        b = get_example_static_wo_hash_zdc().encode()
        response = self._post(reverse(self.view_name),
                              data={"uploadfile":
                                    io.BytesIO(b)
                                    }
                              )

        self.assertEqual(response.reason_phrase,
                         "A static container requires a hash.")
        self.assertEqual(response.status_code, 400)

        b = get_example_static_wrong_hash_zdc().encode()
        response = self._post(reverse(self.view_name),
                              data={"uploadfile":
                                    io.BytesIO(b)
                                    }
                              )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.reason_phrase,
                         "A static container requires a hash.")

    def test_update(self):
        self.assertEqual(len(DataSet.objects.filter(id=testuuid)), 0)

        response = self._post(reverse(self.view_name),
                              data={"uploadfile":
                                    io.BytesIO(get_example_zdc().encode())
                                    }
                              )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(DataSet.objects.filter(id=testuuid)), 1)

        b = io.BytesIO(get_example_update_zdc().encode())

        response = self._post(reverse(self.view_name),
                              data={"uploadfile": b}
                              )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(DataSet.objects.filter(id=testuuid)), 1)

    def test_static_conflict(self):
        self.assertEqual(len(DataSet.objects.all()), 0)
        container = get_example_static_zdc()
        b = container.encode()
        response = self._post(reverse(self.view_name),
                              data={"uploadfile": io.BytesIO(b)}
                              )
        self.assertEqual(len(DataSet.objects.all()), 1)
        container["content.json"]["uuid"] = str(uuid.uuid4())
        b = container.encode()
        response = self._post(reverse(self.view_name),
                              data={"uploadfile": io.BytesIO(b)}
                              )
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.reason_phrase,
                         "A static file requires a unique hash, but there is" +
                         " already a file with the same hash and UUID=" +
                         testuuid + ".")

    def test_hdf5_upload(self):
        self.assertEqual(len(DataSet.objects.all()), 0)
        container = get_example_zdc()
        b = io.BytesIO()
        with h5py.File(b, "w") as h5file:
            dset = h5file.create_dataset("content", data=h5py.Empty("f"))
            for key, value in container["content.json"].items():
                dset.attrs.create(key, str(value))

            dset = h5file.create_dataset("meta", data=h5py.Empty("f"))
            for key, value in container["meta.json"].items():
                dset.attrs.create(key, value)
        b.flush()
        b.seek(0)
        response = self._post(reverse(self.view_name),
                              data={"uploadfile": b}
                              )
        self.assertEqual(response.status_code, 501)
        self.assertEqual(response.reason_phrase, "The server does not " +
                                                 "support to parse hdf5 " +
                                                 "files yet.")
