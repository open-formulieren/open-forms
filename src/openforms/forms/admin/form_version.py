from django.contrib import admin

from openforms.forms.models.form_version import FormVersion


@admin.register(FormVersion)
class FormVersionAdmin(admin.ModelAdmin):
    list_display = (
        "form",
        "created",
    )
    list_filter = ("form", "created")
    search_fields = ("form", "created")

    def has_add_permission(self, request):
        return False
