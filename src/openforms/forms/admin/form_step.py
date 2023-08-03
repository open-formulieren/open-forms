from django.contrib import admin

from ..models import FormStep


@admin.register(FormStep)
class FormStepAdmin(admin.ModelAdmin):
    list_display = ("uuid", "form", "slug", "form_definition")
    list_select_related = ("form", "form_definition")
    search_fields = ("uuid", "slug", "form__uuid", "form__slug")
    raw_id_fields = ("form", "form_definition")
