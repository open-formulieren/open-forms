from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from ..client import Table, TableItem


class ReferenceListsTableSerializer(serializers.Serializer):
    code = serializers.CharField(
        help_text=_("The unique code that identifies the table.")
    )
    name = serializers.CharField(help_text=_("The name of the table."))
    is_valid = (
        serializers.SerializerMethodField(  # pyright: ignore[reportAssignmentType]
            help_text=_("Indicates whether or not the table is expired.")
        )
    )

    def get_is_valid(self, attrs: Table) -> bool:
        if attrs.expires_on and (attrs.expires_on < timezone.now()):
            return False
        return True


class ReferenceListsTableItemSerializer(serializers.Serializer):
    code = serializers.CharField(
        help_text=_("The unique code that identifies the item.")
    )
    name = serializers.CharField(help_text=_("The name of the item."))
    is_valid = (
        serializers.SerializerMethodField(  # pyright: ignore[reportAssignmentType]
            help_text=_("Indicates whether or not the item is expired.")
        )
    )

    def get_is_valid(self, attrs: TableItem) -> bool:
        if attrs.expires_on and (attrs.expires_on < timezone.now()):
            return False
        return True
