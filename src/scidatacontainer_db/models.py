from django.db import models
from django.contrib.auth.models import User, Group

import uuid

from guardian.models import UserObjectPermissionBase, GroupObjectPermissionBase
from guardian.shortcuts import get_users_with_perms, get_groups_with_perms

from .utils import MetaDBError


class Keyword(models.Model):
    """
    Model to represent a Keyword of a DataSet.
    """
    id = models.UUIDField(primary_key=True,
                          default=uuid.uuid4,
                          editable=False,
                          help_text="UUID primary key")
    name = models.CharField(max_length=256,
                            help_text="String representation of a keyword")

    def __str__(self):
        return self.name


class Software(models.Model):
    """
    Model to represent a Software package used in a dataset.
    """
    dbid = models.UUIDField(primary_key=True,
                            default=uuid.uuid4,
                            editable=False,
                            help_text="UUID primary_key")
    name = models.CharField(max_length=256,
                            help_text="Name of the Software package")
    version = models.CharField(max_length=256,
                               help_text="Version of the software package")
    id = models.CharField(max_length=256,
                          help_text="Identifier of the software package")
    id_type = models.CharField(max_length=256,
                               help_text="Type of the given identifier")

    @classmethod
    def to_Software(cls, pt):
        """
        Convert a dictionary as found in a ZDC container into a
        :model:`scidatacontainer_db.Software` instance.
        """
        assert isinstance(pt, dict)
        assert "name" in pt, "usedSoftware requires name attribute."
        assert "version" in pt, "usedSoftware requires version attribute."

        if "id" in pt:
            assert "idType" in pt, "usedSoftware requires idType if " +\
                                   "id is given"
            id = pt["id"]
            id_type = pt["idType"]
        else:
            id = ""
            id_type = ""

        obj, _ = cls.objects.get_or_create(name=pt["name"],
                                           version=pt["version"],
                                           id=id, id_type=id_type)
        return obj


class File(models.Model):
    """
    Model to represent a File from the content of a dataset.
    If the file is a JSON file, the content will be saved, too.
    """
    id = models.UUIDField(primary_key=True,
                          default=uuid.uuid4,
                          editable=False,
                          help_text="UUID primary key")
    name = models.CharField(max_length=256,
                            help_text="File name inside the ZDC dataset")
    size = models.IntegerField(help_text="File size in bytes")
    content = models.JSONField(null=True,
                               blank=True,
                               help_text="Dictionary containing the content " +
                                         "of a JSON file")


class ContainerType(models.Model):
    """
    Model to represent the container type of a dataset.
    """
    dbid = models.UUIDField(primary_key=True,
                            default=uuid.uuid4,
                            editable=False,
                            help_text="UUID primary key")
    name = models.CharField(max_length=256,
                            help_text="Name of the container type")
    id = models.CharField(max_length=256,
                          null=True,
                          blank=True,
                          help_text="Identifier of the container type")
    version = models.CharField(max_length=256,
                               null=True,
                               blank=True,
                               help_text="Version of the container type")

    def __str__(self):
        if self.version:
            return self.name + ", v" + self.version
        return self.name

    @classmethod
    def to_ContainerType(cls, pt):
        """
        Convert a dictionary as found in a ZDC container into a
        :model:`scidatacontainer_db.ContainerType` instance.
        """
        if isinstance(pt, str):
            obj, _ = cls.objects.get_or_create(name=pt, id=None, version=None)
            return obj
        else:
            assert isinstance(pt, dict), "ContainerType needs to be a " +\
                                         "string (name) or a dictionary."
            assert "name" in pt, "ContainerType requires name attribute."

            if "id" in pt:
                assert "version" in pt, "ContainerType requires version" +\
                                        "attribute if id is given"

            id = pt.get("id", None)
            version = pt.get("version", None)
            obj, _ = cls.objects.get_or_create(name=pt["name"],
                                               id=id,
                                               version=version)
            return obj


class DataSetBase(models.Model):
    """
    Base Model of a :model:`scidatacontainer_db.DataSet`. It is required for
    DataSets that are unknown to the server. For example if an unknown ID is
    found in the :model:`scidatacontainer_db.DataSetBase`.replaces attribute,
    an instance of DataSetBase is created. It can be later on replaced by
    uploading this dataset without breaking the relations imposed by
    replaced_by or replaces.
    """
    id = models.UUIDField(primary_key=True,
                          default=uuid.uuid4,
                          editable=False,
                          help_text="UUID primary key")
    _replaced_by_field = models.OneToOneField("self",
                                              related_name="_replaces_field",
                                              blank=True, null=True,
                                              on_delete=models.PROTECT,
                                              help_text="Other instance that" +
                                                        " replaces this " +
                                                        "instance. Don't use" +
                                                        " this field but the" +
                                                        " getter and setter " +
                                                        "functions"
                                              )

    @property
    def is_replaced(self) -> bool:
        """
        Returna true if the model instance is replaced by another DataSet.
        """
        return isinstance(self._replaced_by_field, DataSetBase)

    @property
    def replaced_by(self):
        """
        Other object that replaces this instance. This might be None.
        """
        if self.is_replaced:
            return self._dataset_class_selector(self._replaced_by_field)
        else:
            return None

    @replaced_by.setter
    def replaced_by(self, value):
        self._replaced_by_field = value

    @property
    def replaces(self):
        """
        Other object that is replaced by this instance. This might by None.
        """
        try:
            return self._dataset_class_selector(self._replaces_field)
        except DataSetBase._replaces_field.RelatedObjectDoesNotExist:
            return None

    @replaces.setter
    def replaces(self, replaced_object):
        if replaced_object.is_replaced and\
                (replaced_object.replaced_by.id != self.id):
            raise MetaDBError({"error_code": 409,
                               "msg": "Failed to insert replacement " +
                                      "relationship. The object UUID=" +
                                      str(replaced_object.id) + " is already" +
                                      " replaced by UUID=" +
                                      str(replaced_object.replaced_by.id) +
                                      ". You might want to replace this " +
                                      "dataset.",
                               "object": replaced_object.replaced_by})
        replaced_object.replaced_by = self
        replaced_object.save()


class DataSet(DataSetBase):
    """
    Representation of a ZDC dataset after parsing.
    """
    class Meta:
        permissions = (
                ("view_dataset", "Read only access"),
                ("change_dataset", "Read and write access"),
                )
        default_permissions = ()

    owner = models.ForeignKey(User, on_delete=models.PROTECT,
                              related_name="owner_of",
                              blank=True,
                              help_text="Owner of the dataset")

    # database information
    upload_time = models.DateTimeField(auto_now_add=True,
                                       blank=True,
                                       help_text="Datetime of server uplaod")

    complete = models.BooleanField(help_text="Complete flag to ensure " +
                                             "overwrite protection")
    valid = models.BooleanField(help_text="Valid flag to mark erroneous " +
                                          "datasets")
    invalidation_comment = models.TextField(blank=True,
                                            default="",
                                            help_text="Comment to describe " +
                                                      "why this dataset is " +
                                                      "invalid")
    size = models.IntegerField(help_text="Size of the dataset in bytes")
    server_path = models.CharField(max_length=512,
                                   null=True,
                                   blank=True,
                                   help_text="File path to find the file " +
                                             "on the server")

    # content.json
    created = models.DateTimeField(help_text="Creation timestamp of the " +
                                             "container")
    storage_time = models.DateTimeField(help_text="Timestamp of storage" +
                                                  " of the container")
    static = models.BooleanField(default=False,
                                 help_text="Flag for static containers")
    container_type = models.ForeignKey(ContainerType,
                                       on_delete=models.PROTECT,
                                       related_name="instances",
                                       help_text="ContainerType of this " +
                                                 "dataset")
    hash = models.CharField(max_length=256,
                            null=True,
                            blank=True,
                            help_text="Hash of the container")
    used_software = models.ManyToManyField(Software,
                                           related_name="used_by",
                                           blank=True,
                                           help_text="List of software " +
                                                     "packages used in the " +
                                                     "dataset")
    model_version = models.CharField(max_length=256,
                                     help_text="Version of the data model")

    # meta.json
    author = models.CharField(max_length=256)
    email = models.EmailField()
    organization = models.CharField(max_length=1024, blank=True,
                                    help_text="Affiliation of the author")
    comment = models.TextField(blank=True)
    title = models.CharField(max_length=256)
    keywords = models.ManyToManyField(Keyword,
                                      blank=True,
                                      help_text="List of keywords")
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(blank=True, null=True)
    doi = models.CharField(max_length=512, blank=True)
    license = models.TextField(blank=True,
                               help_text="Name or text of the license")

    # content files
    content = models.ManyToManyField(File,
                                     related_name="included_in",
                                     help_text="List of files included in " +
                                               "the container")

    def get_read_perm_user_list(self):
        """
        Get a list of users that have read only permission for this object.
        """
        return get_users_with_perms(self, with_group_users=False,
                                    only_with_perms_in=["view_dataset"])

    def get_read_perm_group_list(self):
        """
        Get a list of groups that have read only permission for this object.
        """
        perms = get_groups_with_perms(self, attach_perms=True)
        groupnames = [name for name, p in perms.items() if "view_dataset" in p]
        return Group.objects.filter(name__in=groupnames)

    def get_write_perm_user_list(self):
        """
        Get a list of users that have read and write permission for this
        object.
        """
        return get_users_with_perms(self, with_group_users=False,
                                    only_with_perms_in=["change_dataset"])

    def get_write_perm_group_list(self):
        """
        Get a list of groups that have read and write permission for this
        object.
        """
        perms = get_groups_with_perms(self, attach_perms=True)
        groupnames = [name for name, p in perms.items()
                      if "change_dataset" in p]
        return Group.objects.filter(name__in=groupnames)

    def update_attributes(self, d, user):
        """
        Update a :model:`scidatacontainer_db.DataSet` instance with the
        information in the dictionary d. It first ensures that the user is the
        owner of the DataSet.
        """
        if (not user.has_perm("change_dataset", self)) and\
                (self.owner != user):
            raise MetaDBError(
                {"error_code": 403,
                 "msg": "You don't have permission to update this dataset."})

        if self.complete:
            raise MetaDBError({"error_code": 409,
                               "msg": "Dataset is marked complete. " +
                                      "No further changes allowed."})

        if "static" in d:
            if d["static"]:
                if "hash" not in d:
                    raise MetaDBError({"error_code": 400,
                                       "msg": "A static dataset requires " +
                                              "the hash attribute."})
                sobj = DataSet.objects.filter(hash=d["hash"], static=True)

                if len(sobj) != 0:
                    obj = sobj[0]
                    raise MetaDBError({"error_code": 301,
                                       "msg": "A static file requires a " +
                                              "unique hash, but there is " +
                                              "already a file with the same " +
                                              "hash and UUID=" + str(obj.id) +
                                              ".",
                                       "object": obj})

        if self.storage_time:
            if self.storage_time > d["storage_time"]:
                raise MetaDBError({"error_code": 400,
                                   "msg": "Server version of the dataset is" +
                                          " newer than the file you tried " +
                                          "to upload."})

        self.valid = True
        _keys = []
        for key, value in d.items():
            if key == "replaces":
                continue
            else:
                fieldtype = DataSet._meta.get_field(key).get_internal_type()

            if fieldtype == "ManyToManyField":
                # has to be set after save()
                _keys.append(key)
            else:
                setattr(self, key, value)

        self.save()

        if "replaces" in d:
            self.replaces = d["replaces"]

        for key in _keys:
            value = d[key]
            if value and value != []:
                exec("self." + key + ".set(value)")

        self.save()
        return self


def _dataset_class_selector(self, obj):
    """
    Takes a :model:`scidatacontainer_db.DataSetBase` object and returns the
    corresponding :model:`scidatacontainer_db.DataSet` if it exists. Otherwise
    the :model:`scidatacontainer_db.DataSetBase` instance is returned.
    """
    try:
        return DataSet.objects.get(id=obj.id)
    except DataSet.DoesNotExist:
        return obj


DataSetBase._dataset_class_selector = _dataset_class_selector


"""
Classes to make permission checks faster:
https://django-guardian.readthedocs.io/en/stable/userguide/performance.html
"""


class DataSetUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(DataSet, on_delete=models.CASCADE)


class DataSetGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(DataSet, on_delete=models.CASCADE)
