from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html_join
from django.utils.translation import gettext_lazy as _

from furl import furl
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from openforms.forms.models import Category


@admin.register(Category)
class CategoryAdmin(TreeAdmin):
    fields = [
        "name",
        "treebeard_position",
        "treebeard_ref_node",
    ]
    form = movenodeform_factory(Category, fields=fields)
    list_display = [
        "name",
        "form_count",
        "get_object_actions",
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(form_count=Count("form"))
        return qs

    @admin.display(description=_("form count"))
    def form_count(self, category: Category):
        return category.form_count

    @admin.display(description=_("Actions"))
    def get_object_actions(self, obj) -> str:
        form_list_url = furl(reverse("admin:forms_form_changelist"))
        form_list_url.args["category"] = obj.id
        links = ((str(form_list_url), _("Show forms")),)
        return format_html_join(" | ", '<a href="{}" target="_blank">{}</a>', links)
