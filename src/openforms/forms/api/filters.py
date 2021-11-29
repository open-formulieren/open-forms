from django.utils.translation import gettext as _

from django_filters import rest_framework as filters

from ..models import FormLogic, FormPriceLogic


class FormLogicBaseFilter(filters.FilterSet):
    form = filters.UUIDFilter(
        field_name="form__uuid",
        label=_("The UUID of a form associated with logic rules"),
    )

    class Meta:
        fields = ["form"]


class FormLogicFilter(FormLogicBaseFilter):
    class Meta(FormLogicBaseFilter.Meta):
        model = FormLogic


class FormPriceLogicFilter(FormLogicBaseFilter):
    class Meta(FormLogicBaseFilter.Meta):
        model = FormPriceLogic
