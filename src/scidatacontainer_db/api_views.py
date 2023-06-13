from django.contrib.auth.models import User, Group
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.viewsets import ReadOnlyModelViewSet

from guardian.shortcuts import get_objects_for_user, remove_perm, assign_perm

from django_filters.rest_framework import DjangoFilterBackend
from django_filters.rest_framework import FilterSet

from .models import ContainerType, DataSet, File, Keyword, Software
from .parsers import parse_container_file
from .utils import ensure_read_permission, ensure_owner, MetaDBError,\
                   APIResponse as Response
from .test_utils import download_test_dataset, get_test_data
from . import serializers


charfield_filters = ["contains", "icontains", "exact", "iexact",
                     "startswith", "istartswith",
                     "endswith", "iendswith", "regex", "iregex"]


datefield_filter = ["exact", "year__gt", "year__lt", "month__gt",
                    "month__lt", "day__gt", "day__lt"]


class DataSetFilter(FilterSet):
    class Meta:
        model = DataSet
        fields = {
                 "title": charfield_filters,
                 "id": charfield_filters,
                 "upload_time": datefield_filter,
                 "author": charfield_filters,
                 "comment": charfield_filters,
                 "description": charfield_filters,
                 "email": charfield_filters,
                 "created": datefield_filter,
                 "storage_time": datefield_filter,
                 # "container_type": charfield_filters,
                 }


class DataSetViewSet(ReadOnlyModelViewSet, mixins.CreateModelMixin):
    serializer_class = serializers.DataSetSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DataSetFilter
    filterset_fields = ["title", "id"]
    queryset = DataSet.objects.all()

    def get_queryset(self):
        user = self.request.user
        q = get_objects_for_user(user, "view_dataset", DataSet) |\
            user.owner_of.all()
        return q.filter(valid=True)

    def create(self, request):
        if len(request.FILES) > 0:
            try:
                parse_container_file(request.FILES["uploadfile"], request.user)
            except MetaDBError as e:
                obj = e.args[0].get("object", False)
                if obj:
                    s = self.serializer_class(obj,
                                              context={'request': request})
                    return Response(s.data,
                                    status=e.args[0]["error_code"],
                                    reason=e.args[0]["msg"])

                return Response(e.args[0]["msg"],
                                status=e.args[0]["error_code"],
                                reason=e.args[0]["msg"])

            return Response(status=201)
        return Response("", status=400,
                        reason="No data file found in your request!")

    def patch(self, request, pk=None):
        dataset = get_object_or_404(DataSet, id=pk)

        ensure_owner(request.user, dataset)

        accepted_fields = ["readonly_users", "readwrite_users",
                           "readonly_groups", "readwrite_groups",
                           "owner", "valid"]
        rejected = []
        d = {}
        for key, value in request.data.items():
            if key not in accepted_fields:
                rejected.append(key)
            else:
                d[key] = value

        if len(rejected) != 0:
            return Response("", status=400,
                            reason="The follwoing fields must not be " +
                            "updated: '" + "', '".join(rejected) + "'.")

        errors = []

        if "readonly_users" in d:
            for user in dataset.get_read_perm_user_list():
                remove_perm("view_dataset", user, dataset)

            ro_users = d["readonly_users"]
            if not isinstance(ro_users, list):
                ro_users = [ro_users]
            for user in ro_users:
                try:
                    user_obj = User.objects.get(username=user)
                    remove_perm("change_dataset", user_obj, dataset)
                    assign_perm("view_dataset", user_obj, dataset)
                except User.DoesNotExist:
                    errors.append("User " + user + " does not exist")

        if "readwrite_users" in d:
            for user in dataset.get_write_perm_user_list():
                remove_perm("change_dataset", user, dataset)

            rw_users = d["readwrite_users"]
            if not isinstance(rw_users, list):
                rw_users = [rw_users]
            for user in rw_users:
                try:
                    user_obj = User.objects.get(username=user)
                    remove_perm("view_dataset", user_obj, dataset)
                    assign_perm("change_dataset", user_obj, dataset)
                except User.DoesNotExist:
                    errors.append("Error: User " + user + " does not exist")

        if "readonly_groups" in d:
            for group in dataset.get_read_perm_group_list():
                remove_perm("view_dataset", group, dataset)

            ro_groups = d["readonly_groups"]
            if not isinstance(ro_groups, list):
                ro_groups = [ro_groups]
            for group in ro_groups:
                try:
                    group_obj = Group.objects.get(name=group)
                    remove_perm("change_dataset", group_obj, dataset)
                    assign_perm("view_dataset", group_obj, dataset)
                except Group.DoesNotExist:
                    errors.append("Group " + group + " does not exist")

        if "readwrite_groups" in d:
            for group in dataset.get_write_perm_group_list():
                remove_perm("change_dataset", group, dataset)

            rw_groups = d["readwrite_groups"]
            if not isinstance(rw_groups, list):
                rw_groups = [rw_groups]
            for group in rw_groups:
                try:
                    group_obj = Group.objects.get(name=group)
                    remove_perm("view_dataset", group_obj, dataset)
                    assign_perm("change_dataset", group_obj, dataset)
                except Group.DoesNotExist:
                    errors.append("Group " + group + " does not exist")

        if "owner" in d:
            try:
                user_obj = User.objects.get(username=d["owner"])
                dataset.owner = user_obj
                dataset.save()
            except User.DoesNotExist:
                errors.append("New owner " + d["owner"] + " does not exist")

        if "valid" in d:
            if d["valid"] and (not dataset.valid):
                errors.append("It is not possible to change the status of a " +
                              "dataset from invalid to valid.")
                return Response("", 400, reason="\n".join(errors))
            dataset.valid = d["valid"]
            dataset.save()
        return Response("", status=200, reason="\n".join(errors))

    def retrieve(self, request, pk=None, status_code=200, redirect=True):
        try:
            obj = DataSet.objects.get(id=pk)
        except DataSet.DoesNotExist:
            if pk.startswith("00000000-0000-0000-0000-00000000"):
                obj = get_test_data(pk)
            else:
                return Response("", status=404,
                                reason="No DataSet with UUID=" +
                                pk + " found!")
        if not obj.valid:
            return Response({"id": str(obj.id),
                             "owner": obj.owner.username,
                             "invalidation_comment": obj.invalidation_comment},
                            status=204, reason="DataSet was deleted!")

        ensure_read_permission(request.user, obj)
        if redirect and obj.is_replaced:
            pk = obj.replaced_by.id
            return self.retrieve(request, pk=pk, status_code=301,
                                 redirect=True)

        serializer = self.get_serializer(obj)
        return Response(serializer.data, status=status_code)

    @action(methods=["get"], detail=True, url_path="noredirect",
            url_name="detail-noredirect")
    def retrieve_noredirect(self, request, pk=None):
        return self.retrieve(request, pk=pk, status_code=200, redirect=False)

    @action(methods=["get"], detail=True, url_path="download",
            url_name="download")
    def download(self, request, pk=None, status_code=200, redirect=True):
        try:
            obj = DataSet.objects.get(id=pk)
        except DataSet.DoesNotExist:
            if pk.startswith("00000000-0000-0000-0000-00000000"):
                return download_test_dataset(pk)
            else:
                return Response("", status=404,
                                reason="No DataSet with UUID=" +
                                pk + " found!")

        if not obj.valid:
            r = Response("", status=204)
            return Response("", status=204, reason="DataSet was deleted!")

        ensure_read_permission(request.user, obj)
        if redirect and obj.is_replaced:
            pk = obj.replaced_by.id
            return self.download(request, pk=pk, status_code=301)

        r = FileResponse(open(obj.server_path, 'rb'))
        r.status_code = status_code
        return r

    @action(methods=["get"], detail=True, url_path="download/noredirect",
            url_name="download-noredirect")
    def download_noredirect(self, request, pk=None):
        return self.download(request, pk=pk, status_code=200, redirect=False)


class PermissionFilteredReadOnlyViewSet(ReadOnlyModelViewSet):
    def get_queryset(self):
        user = self.request.user
        q = get_objects_for_user(user, "view_dataset", DataSet) |\
            user.owner_of.all()
        ids = q.values_list(self.dataset_fieldname + "__" + self.idstr)
        return self.model.objects.filter(**{self.idstr + "__in": ids})


class ContainerTypeViewSet(PermissionFilteredReadOnlyViewSet):
    serializer_class = serializers.ContainerTypeSerializer
    model = ContainerType
    dataset_fieldname = "container_type"
    idstr = "dbid"


class FileViewSet(PermissionFilteredReadOnlyViewSet):
    serializer_class = serializers.FileSerializer
    model = File
    dataset_fieldname = "content"
    idstr = "id"


class KeywordViewSet(PermissionFilteredReadOnlyViewSet):
    serializer_class = serializers.KeywordSerializer
    model = Keyword
    dataset_fieldname = "keywords"
    idstr = "id"


class SoftwareViewSet(PermissionFilteredReadOnlyViewSet):
    serializer_class = serializers.SoftwareSerializer
    model = Software
    dataset_fieldname = "used_software"
    idstr = "dbid"
