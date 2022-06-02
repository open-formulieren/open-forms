from django.contrib import admin
from django.db.models import Count
from django.utils.translation import gettext_lazy as _

from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from openforms.forms.models import Category, Form


@admin.register(Category)
class CategoryAdmin(TreeAdmin):
    fields = [
        "name",
        "_ref_node_id",
        "_position",
    ]
    form = movenodeform_factory(Category, fields=fields)
    list_display = [
        "name",
        "anno_count",
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(anno_count=Count("form"))
        return qs

    def anno_count(self, category=None):
        if not category:
            return
        return getattr(category, "anno_count", 0)

    anno_count.short_description = _("count")
