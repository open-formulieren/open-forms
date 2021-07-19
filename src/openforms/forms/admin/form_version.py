from django.contrib import admin

from openforms.forms.models.form_version import FormVersion


@admin.register(FormVersion)
class FormVersionAdmin(admin.ModelAdmin):
    list_display = (
        "form",
        "date_creation",
    )
    list_filter = ("form", "date_creation")
    search_fields = ("form", "date_creation")

    def has_add_permission(self, request):
        return False
