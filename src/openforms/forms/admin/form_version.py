from django.contrib import admin

from openforms.forms.models.form_version import FormVersion


@admin.register(FormVersion)
class FormVersionAdmin(admin.ModelAdmin):
    list_display = (
        "form",
        "created",
        "app_release",
    )
    list_filter = ("form", "created", "app_release")
    search_fields = ("form__name", "form__internal_name", "created")

    def has_add_permission(self, request):
        return False
