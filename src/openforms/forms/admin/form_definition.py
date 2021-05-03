from django.contrib import admin, messages
from django.contrib.admin import AdminSite
from django.contrib.admin.actions import delete_selected as _delete_selected
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from ..forms import FormDefinitionForm
from ..models import Form, FormDefinition


def delete_selected(modeladmin, request, queryset):
    for name in queryset.exclude(formstep=None).values_list('name', flat=True):
        messages.error(
            request,
            f"{name} mag niet verwijderen omdat het is in een Form gebruikt",
        )
    return _delete_selected(modeladmin, request, queryset.filter(formstep=None))


delete_selected.allowed_permissions = ("delete",)
delete_selected.short_description = _("Delete selected %(verbose_name_plural)s")


class FormDefinitionAdminSite(AdminSite):
    def __init__(self, name="admin"):
        super().__init__(name=name)
        self._actions = {"delete_selected": delete_selected}


@admin.register(FormDefinition)
class FormDefinitionAdmin(admin.ModelAdmin):
    form = FormDefinitionForm
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "used_in_forms")
    actions = ["overridden_delete_selected", "make_copies"]

    def __init__(self, model, admin_site):
        super().__init__(model, FormDefinitionAdminSite())

    def make_copies(self, request, queryset):
        for instance in queryset:
            instance.copy()

    make_copies.short_description = _("Kopie geselecteerde Form Definitions")

    def used_in_forms(self, obj) -> str:
        forms = Form.objects.filter(formstep__form_definition=obj)
        html = "<ul>"
        for form in forms:
            form_url = reverse(
                "admin:forms_form_change",
                kwargs={"object_id": form.pk},
            )
            html += f"<li><a href={form_url}>{form.name}</a></li>"
        html += "</ul>"
        return format_html(html)

    used_in_forms.short_description = _("Gebruikt in forms")
