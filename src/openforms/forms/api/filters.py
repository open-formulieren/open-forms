from django.utils.translation import gettext_lazy as _

from django_filters import rest_framework as filters
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field

from ..models import Form, FormDefinition, FormVariable


class FormVariableFilter(filters.FilterSet):
    class Meta:
        model = FormVariable
        fields = ("source",)


class FormDefinitionFilter(filters.FilterSet):
    used_in = extend_schema_field(OpenApiTypes.UUID)(
        filters.ModelChoiceFilter(
            queryset=Form.objects.all(),
            to_field_name="uuid",
            field_name="formstep__form",
            distinct=True,
            help_text=_("UUID of the form the definition is used in."),
        )
    )

    class Meta:
        model = FormDefinition
        fields = ("is_reusable",)
