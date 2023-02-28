from django.utils.translation import gettext_lazy as _

from django_filters import CharFilter
from django_filters.rest_framework import FilterSet

from openforms.authentication.constants import AuthAttribute
from openforms.submissions.models import Submission


class BSNAuthInfoFilter(FilterSet):
    """
    filter submissions on BSN authentication
    """

    bsn = CharFilter(
        label=_("BSN number"),
        method="filter_bsn",
        required=True,
    )

    def filter_bsn(self, queryset, name, bsn: str):
        return queryset.filter(
            auth_info__value=bsn,
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__attribute_hashed=False,
        )

    class Meta:
        model = Submission
        fields = [
            "bsn",
        ]
