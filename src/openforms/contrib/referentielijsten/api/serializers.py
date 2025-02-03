from datetime import datetime

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
        help_text=_("The timestamp on which the tabel expires."), write_only=True
    )

    is_geldig = serializers.SerializerMethodField(
        help_text=_("Indicates whether or not the table is expired.")
    )

    def get_is_geldig(self, attrs: dict) -> bool:
        if einddatum := attrs.get("einddatumGeldigheid"):
            parsed_datetime = datetime.fromisoformat(einddatum)
            if parsed_datetime < datetime.now(tz=parsed_datetime.tzinfo):
                return False
        return True
