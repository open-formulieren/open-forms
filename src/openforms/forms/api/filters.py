from django.utils.translation import gettext as _

from django_filters import rest_framework as filters

from ..models import FormPriceLogic, FormVariable


class FormLogicBaseFilter(filters.FilterSet):
    form = filters.UUIDFilter(
        field_name="form__uuid",
        label=_("The UUID of a form associated with logic rules"),
    )

    class Meta:
        fields = ["form"]


class FormPriceLogicFilter(FormLogicBaseFilter):
    class Meta(FormLogicBaseFilter.Meta):
        model = FormPriceLogic


class FormVariableFilter(filters.FilterSet):
    class Meta:
        model = FormVariable
        fields = ("source",)
