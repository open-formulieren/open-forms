from django.contrib import admin

from .models import InitialSubmissionData


@admin.register(InitialSubmissionData)
class InitialSubmissionDataAdmin(admin.ModelAdmin):
    list_display = ("form", "representee_auth_attribute", "created_on", "uuid")
    list_filter = ("representee_auth_attribute", "created_on", "form")
    list_select_related = ("form",)
    search_fields = ("uuid", "form__name", "form__internal_name")
    date_hierarchy = "created_on"
    autocomplete_fields = ("form",)
    raw_id_fields = ("used_for_submission",)
