from django.contrib import admin
from django.db.models import Count, ExpressionWrapper, F, IntegerField
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.translation import gettext_lazy as _

from rangefilter.filters import DateRangeFilterBuilder

from ..forms.form_statistics import (
    get_first_of_previous_month,
    get_last_of_previous_month,
)
from ..models import FormSubmissionStatistics
from .views import ExportSubmissionStatisticsView


@admin.register(FormSubmissionStatistics)
class FormSubmissionStatisticsAdmin(admin.ModelAdmin):
    """
    Modified admin view to display the submission statistics for each form.

    The table displays the form name, number of submission and when the first and last
    submission happened _within the selected date range_. We do this by looking at the
    logged events for each completed submission, stored in the django-timeline-logger
    database table with particular metadata.

    Filtering for submissions on date range is possible based on the timestamp.

    If the log events are pruned, this affects the reported statistics. Filtering a date
    range will also show the first/last timestamps within the selected range.

    There are no detail views to click through, the table overview is all you get. If
    you construct the URLs by hand, you end up in the standard timeline log detail page.
    No permissions to create, delete or modify records are enabled.
    """

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
    search_fields = ("extra_data__form_name",)
    show_full_result_count = False

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

    def changelist_view(self, request, extra_context=None):
        # we can't really pass the queryset as just an extra thing because it doesn't
        # apply the changelist filters. So instead, we grab the context from the
        # parent's TemplateResponse and add it.
        response = super().changelist_view(request, extra_context=extra_context)
        assert isinstance(response, TemplateResponse)
        assert response.context_data is not None
        qs = (
            response.context_data["cl"]
            .queryset.annotate(
                form_id=ExpressionWrapper(
                    F("extra_data__form_id"), output_field=IntegerField()
                )
            )
            .exclude(form_id__isnull=True)
            .values("form_id")
            .annotate(
                submission_count=Count("id"),
                form_name=F("extra_data__form_name"),
            )
            .order_by("form_name")
        )
        response.context_data["aggregated_qs"] = qs
        return response
