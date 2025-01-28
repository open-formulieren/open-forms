from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.api.utils import mark_experimental


@mark_experimental
class ReferentielijstTabellenSerializer(serializers.Serializer):
    code = serializers.CharField(
        help_text=_("The unique code that identifies the table.")
    )
    naam = serializers.CharField(help_text=_("The name of the table."))
    einddatumGeldigheid = serializers.DateTimeField(
        help_text=_("The timestamp on which the tabel expires."), allow_null=True
    )
