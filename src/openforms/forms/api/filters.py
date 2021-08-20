from django.utils.translation import gettext as _

from django_filters import rest_framework as filters

from ..models import FormLogic


class FormLogicFilter(filters.FilterSet):
    form = filters.UUIDFilter(
        field_name="form__uuid",
        label=_("The UUID of a form associated with logic rules"),
    )

    class Meta:
        model = FormLogic
        fields = ["form"]
