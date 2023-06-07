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

    class Meta:
        model = DataSetBase
        fields = ["url", "id"]


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

    class Meta:
        model = Software
        fields = ["url", "name", "version", "id", "id_type"]


class ContainerTypeSerializer(serializers.ModelSerializer):

    instances = LinkedDataSetSerializer(many=True)

    class Meta:
        model = ContainerType
        fields = ["name", "id", "version", "instances", "dbid"]


class DataSetSerializer(serializers.ModelSerializer):
    container_type = LinkedContainerTypeSerializer()
    content = LinkedFileSerializer(many=True, read_only=True)
    keywords = LinkedKeywordSerializer(many=True, read_only=True)
    used_software = LinkedSoftwareSerializer(many=True, read_only=True)
    replaces = LinkedDataSetSerializer(read_only=True)

    class Meta:
        model = DataSet
        fields = ["id", "upload_time", "replaces", "complete",
                  "valid", "size", "created", "modified", "static",
                  "container_type", "hash", "used_software", "model_version",
                  "author", "email", "comment", "title", "keywords",
                  "description", "content"]


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
