from django_filters import rest_framework as filters

from openforms.forms.models import Form


class FormCategoryNameFilter(filters.FilterSet):

    class Meta:
        model = Form
        fields = ("category__name",)
