from django.utils.translation import gettext as _

import django_filters

from ..models import FormLogic


class FormLogicFilter(django_filters.FilterSet):
    form = django_filters.UUIDFilter(
        field_name="form__uuid",
        label=_("The UUID of a form associated with logic rules"),
    )

    class Meta:
        model = FormLogic
        fields = ["form"]
