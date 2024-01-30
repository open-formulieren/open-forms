from django.contrib import admin

from ..models import FormStatistics


@admin.register(FormStatistics)
class FormStatisticsAdmin(admin.ModelAdmin):
    list_display = (
        "form_name",
        "submission_count",
        "first_submission",
        "last_submission",
    )
    fields = (
        "form",
        "form_name",
        "submission_count",
        "first_submission",
        "last_submission",
    )

    search_fields = ("form_name",)
    date_hierarchy = "last_submission"
    list_filter = ("last_submission", "first_submission")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
