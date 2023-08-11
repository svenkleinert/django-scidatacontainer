from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import FileResponse

import io
from uuid import uuid4

from scidatacontainer.tests import get_test_container

from .parsers import BaseParser
from .serializers import DataSetSerializer
from .utils import APIResponse, MetaDBError


class ContainerObjectParser(BaseParser):
    def _read_content_json(self):
        # filename is a Container object in this case
        self.content = self.filename["content.json"]

    def _read_meta_json(self):
        # filename is a Container object in this case
        self.meta = self.filename["meta.json"]

    def _read_filelist(self):
        self.filename.size = 42
        self.files = []


def api_detail_test_data(uuid: str, user: User, serializer):
    if uuid.endswith("204"):
        return APIResponse(status=204, reason="DataSet was deleted")

    if uuid.endswith("404"):
        return APIResponse(status=404, reason="No DataSet with UUID=" +
                                                  uuid + " found!")

    if uuid.endswith("403"):
        raise PermissionDenied

    container = get_test_container()
    status_code = 200
    if uuid.endswith("301"):
        container["content.json"]["replaces"] = uuid
        status_code = 301

    parser = ContainerObjectParser()
    container["content.json"]["uuid"] = str(uuid4())
    obj = parser.parse(container, user)
    obj.doi = "https://example.com/" + uuid

    s = serializer(obj)

    r = APIResponse(s.data, status=status_code)

    if obj.replaces:
        obj.replaces.delete()

    obj.delete()

    return r


def download_test_dataset(uuid: str):
    if uuid.endswith("204"):
        return APIResponse("", status=204, reason="DataSet was deleted")

    if uuid.endswith("404"):
        return APIResponse('', status=404, reason="No DataSet with UUID=" +
                                                  uuid + " found!")

    if uuid.endswith("403"):
        raise PermissionDenied

    container = get_test_container()
    if uuid.endswith("301"):
        container["content.json"]["replaces"] = uuid
        r = FileResponse(io.BytesIO(container.encode()))
        r.status_code = 301
        return r

    r = FileResponse(io.BytesIO(container.encode()))
    r.status_code = 200
    return r
