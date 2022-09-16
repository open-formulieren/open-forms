from django_filters import rest_framework as filters

from ..models import FormVariable


class FormVariableFilter(filters.FilterSet):
    class Meta:
        model = FormVariable
        fields = ("source",)
