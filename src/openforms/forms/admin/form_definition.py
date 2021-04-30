from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from ..forms import FormDefinitionForm
from ..models import Form, FormDefinition


@admin.register(FormDefinition)
class FormDefinitionAdmin(admin.ModelAdmin):
    form = FormDefinitionForm
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "used_in_forms")

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

    used_in_forms.short_description = _("Used in forms")
