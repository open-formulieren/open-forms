from django.contrib import admin
from django.urls import path
from django.utils.translation import gettext_lazy as _

from rangefilter.filters import DateRangeFilterBuilder

from ..forms.form_statistics import (
    get_first_of_previous_month,
    get_last_of_previous_month,
)
from ..models import FormStatistics, FormSubmissionStatisticsV2
from .views import ExportSubmissionStatisticsView


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

    def get_urls(self):
        urls = super().get_urls()
        export_view = self.admin_site.admin_view(
            ExportSubmissionStatisticsView.as_view(
                media=self.media,
            )  # pyright: ignore[reportArgumentType]
        )
        custom_urls = [
            path("export/", export_view, name="formstatistics_export"),
        ]
        return custom_urls + urls


@admin.register(FormSubmissionStatisticsV2)
class FormSubmissionStatisticsV2Admin(admin.ModelAdmin):
    list_display = (
        "form_name",
        "timestamp",
    )
    list_filter = (
        (
            "timestamp",
            DateRangeFilterBuilder(
                title=_("submitted between"),
                default_start=lambda *args: get_first_of_previous_month(),
                default_end=lambda *args: get_last_of_previous_month(),
            ),
        ),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description=_("form name"))
    def form_name(self, obj: FormSubmissionStatisticsV2) -> str:
        # if we have snapshot data, use it
        if not (form_name := obj.extra_data.get("form_name", "")):
            return "- unknown -"
        return form_name
