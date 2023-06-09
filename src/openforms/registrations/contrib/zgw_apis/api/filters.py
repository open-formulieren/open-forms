from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from openforms.api.fields import PrimaryKeyRelatedAsChoicesField

from ..models import ZGWApiGroupConfig


class ZgwApiGroupFilterSerializer(serializers.Serializer):
    zgw_api_group = PrimaryKeyRelatedAsChoicesField(
        queryset=ZGWApiGroupConfig.objects.all(),
        help_text=_(
            "The primary key of the ZGW API set to use. If provided, the informatieobjecttypen from the Catalogi API "
            "in this set will be returned. Otherwise, the Catalogi API in the default ZGW API set will be returned."
        ),
        label=_("ZGW API set"),
        required=False,
    )
