from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from django_filters import rest_framework as filters
from django_filters.constants import EMPTY_VALUES
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
        or_fields = ("is_reusable", "used_in")

    def filter_queryset(self, queryset):
        """
        Override base implementation to add OR-behaviour instead of the standard AND.

        See https://github.com/carltongibson/django-filter/discussions/1426
        """
        _or = Q()

        for name in self.Meta.or_fields:
            # this essentially re-implements django_filters.filters.Filter.filter,
            # as otherwise we would have to introspect private django query/queryset API
            # *shudders*
            or_filter_value = self.form.cleaned_data.pop(name)
            if or_filter_value in EMPTY_VALUES:
                continue
            or_filter = self.filters[name]
            if or_filter.distinct:
                queryset = queryset.distinct()
            lookup = "%s__%s" % (or_filter.field_name, or_filter.lookup_expr)
            q_expr = Q(**{lookup: or_filter_value})
            if or_filter.exclude:
                q_expr = ~q_expr
            _or |= q_expr

        if _or:
            queryset = queryset.filter(_or)
        return super().filter_queryset(queryset)
