from rest_framework import serializers

from .models import ContainerType, DataSet, DataSetBase, File, Keyword,\
                    Software


class LinkedContainerTypeSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
            view_name="scidatacontainer_db:api:containertype-detail")

    class Meta:
        model = ContainerType
        fields = ["url", "name", "id", "version"]


class LinkedDataSetSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
            view_name="scidatacontainer_db:api:dataset-detail")
    uuid = serializers.UUIDField(source="id")

    class Meta:
        model = DataSetBase
        fields = ["url", "uuid"]


class LinkedFileSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
            view_name="scidatacontainer_db:api:file-detail")

    class Meta:
        model = File
        fields = ["url", "name", "size"]


class LinkedKeywordSerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.HyperlinkedIdentityField(
            view_name="scidatacontainer_db:api:keyword-detail")

    class Meta:
        model = File
        fields = ["url", "name"]


class LinkedSoftwareSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
            view_name="scidatacontainer_db:api:software-detail")
    idType = serializers.CharField(source="id_type")

    class Meta:
        model = Software
        fields = ["url", "name", "version", "id", "idType"]


class ContainerTypeSerializer(serializers.ModelSerializer):

    instances = LinkedDataSetSerializer(many=True)

    class Meta:
        model = ContainerType
        fields = ["name", "id", "version", "instances", "dbid"]


class DataSetSerializer(serializers.ModelSerializer):
    containerType = LinkedContainerTypeSerializer(source="container_type")
    content = LinkedFileSerializer(many=True, read_only=True)
    keywords = LinkedKeywordSerializer(many=True, read_only=True)
    usedSoftware = LinkedSoftwareSerializer(
                                            many=True,
                                            read_only=True,
                                            source="used_software")
    replaces = LinkedDataSetSerializer(read_only=True)
    uuid = serializers.UUIDField(source="id")
    storageTime = serializers.DateTimeField(source="storage_time")

    class Meta:
        model = DataSet
        fields = ["uuid", "upload_time", "replaces", "complete",
                  "valid", "size", "created", "storageTime", "static",
                  "containerType", "hash", "usedSoftware", "model_version",
                  "author", "email", "comment", "title", "keywords",
                  "description", "organization", "doi", "license", "timestamp",
                  "content"]


class FileSerializer(serializers.ModelSerializer):
    included_in = LinkedDataSetSerializer(many=True)

    class Meta:
        model = File
        fields = "__all__"


class KeywordSerializer(serializers.ModelSerializer):

    class Meta:
        model = Keyword
        fields = "__all__"


class SoftwareSerializer(serializers.ModelSerializer):
    used_by = LinkedDataSetSerializer(many=True)

    class Meta:
        model = Software
        fields = "__all__"
