from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.reverse import reverse

from openforms.submissions.models import TemporaryFileUpload

from .validators import MimeTypeValidator, NoVirusValidator


class TemporaryFileUploadSerializer(serializers.Serializer):
    """
    https://help.form.io/integrations/filestorage/#url

    {
        url: 'http://link.to/file',
        name: 'The_Name_Of_The_File.doc',
        size: 1000
    }
    """

    file = serializers.FileField(
        write_only=True,
        required=True,
        use_url=False,
        validators=[MimeTypeValidator(), NoVirusValidator()],
    )

    url = serializers.SerializerMethodField(
        label=_("URL"), source="get_url", read_only=True
    )
    name = serializers.CharField(
        label=_("File name"), source="file_name", read_only=True
    )
    size = serializers.IntegerField(
        label=_("File size"), source="content.size", read_only=True
    )

    class Meta:
        model = TemporaryFileUpload
        fields = (
            "url",
            "name",
            "size",
        )

    def get_url(self, instance) -> str:
        request = self.context["request"]
        return reverse(
            "api:submissions:temporary-file",
            kwargs={"uuid": instance.uuid},
            request=request,
        )


class MapSearchLatLng(serializers.Serializer):
    lat = serializers.FloatField(label=_("Latitude"))
    lng = serializers.FloatField(label=_("Longitude"))


class MapSearchRD(serializers.Serializer):
    x = serializers.FloatField(label=_("X"))
    y = serializers.FloatField(label=_("Y"))


class MapSearchSerializer(serializers.Serializer):
    label = serializers.CharField(label=_("weergave naam"))
    latLng = MapSearchLatLng()
    rd = MapSearchRD()
