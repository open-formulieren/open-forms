from datetime import datetime

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from ..client import Tabel


class ReferentielijstTabellenSerializer(serializers.Serializer):
    code = serializers.CharField(
        help_text=_("The unique code that identifies the table.")
    )
    naam = serializers.CharField(help_text=_("The name of the table."))
    is_geldig = serializers.SerializerMethodField(
        help_text=_("Indicates whether or not the table is expired.")
    )

    def get_is_geldig(self, attrs: Tabel) -> bool:
        if einddatum := attrs.get("einddatumGeldigheid"):
            parsed_datetime = datetime.fromisoformat(einddatum)
            if parsed_datetime < timezone.now():
                return False
        return True


class ReferentielijstTabelItemsSerializer(serializers.Serializer):
    code = serializers.CharField(
        help_text=_("The unique code that identifies the item.")
    )
    naam = serializers.CharField(help_text=_("The name of the item."))
    is_geldig = serializers.SerializerMethodField(
        help_text=_("Indicates whether or not the item is expired.")
    )

    def get_is_geldig(self, attrs: Tabel) -> bool:
        if einddatum := attrs.get("einddatumGeldigheid"):
            parsed_datetime = datetime.fromisoformat(einddatum)
            if parsed_datetime < timezone.now():
                return False
        return True
