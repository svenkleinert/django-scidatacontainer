from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User

from rest_framework.response import Response


def ensure_read_permission(user: User, dataset):
    """
    Checks if the user has read permission for a given DataSet. Raises a
    PermissionDenied Exception otherwise.

    :param user: User object of requesting user.
    :param dataset: DataSet that the user wants to read.

    :raises django.core.exceptions.PermissionDenied: If the user doesn't have
    read permissions.
    """
    if user == dataset.owner:
        return
    if user.has_perm("view_dataset", dataset):
        return
    if user.has_perm("change_dataset", dataset):
        return
    raise PermissionDenied


def ensure_owner(user: User, dataset):
    """
    Checks if the user is the owner of a given DataSet. Raises a
    PermissionDenied Exception otherwise.

    :param user: User object of requesting user.
    :param dataset: DataSet to check the ownership.

    :raises django.core.exceptions.PermissionDenied: If the user isn't the
    owner.
    """
    if user == dataset.owner:
        return
    raise PermissionDenied


class APIResponse(Response):
    """
    Custom Response derived from rest_framewort.response.Response to set
    the reason phrase on creation of the response.
    """
    def __init__(self, data=None, status=None, template_name=None,
                 headers=None, exception=False, content_type=None,
                 reason=None):

        super().__init__(data=data, status=status, template_name=template_name,
                         headers=headers, exception=False, content_type=None)
        if reason:
            self.reason_phrase = reason


class MetaDBError(Exception):
    """
    Excetption raised by various function and caught by the request handling
    views. The status code and reason_phrase stored in the instances will be
    part of the response.
    """
    pass
