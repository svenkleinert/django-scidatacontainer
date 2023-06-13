from django.core.exceptions import PermissionDenied
from django.http import FileResponse

import io

from scidatacontainer.tests import get_test_container

from .utils import APIResponse, MetaDBError
from .models import DataSet


def parse_test_data(uuid: str):
    """
    Check the last characters of a test UUID and raise a corresponding
    exception.

    :param uuid: UUID as str

    :raises scidatacontainer_db.MetaDBError: The exception matching the error
    code of the last 3 characters of the UUID.
    """
    if uuid.endswith("409"):
        raise MetaDBError({"error_code": 409,
                           "msg": "Dataset is marked complete. " +
                                  "No further changes allowed."})
    if uuid.endswith("403"):
        raise MetaDBError(
            {"error_code": 403,
             "msg": "You don't have permission to update this dataset."})

    if uuid.endswith("301"):
        pass


def get_test_data(uuid: str):
    dc = get_test_container()

    if uuid.endswith("301"):
        dc.freeze()
        DataSet(uuid=uuid.uuid4())
    return


def download_test_dataset(uuid: str):
    if uuid.endswith("204"):
        return APIResponse("", status=204, reason="DataSet was deleted")

    if uuid.endswith("404"):
        return APIResponse("", status=404, reason="No DataSet with UUID=" +
                                                  uuid + "found!")

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
