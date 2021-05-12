from django.contrib import admin, messages
from django.utils.html import format_html_join
from django.utils.translation import gettext_lazy as _

from .exports import export_submissions
from .models import Submission, SubmissionStep


class SubmissionStepInline(admin.StackedInline):
    model = SubmissionStep
    extra = 0
    fields = (
        "uuid",
        "form_step",
        "data",
    )


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    date_hierarchy = "completed_on"
    list_display = (
        "form",
        "completed_on",
    )
    list_filter = ("form",)
    search_fields = ("form__name",)
    inlines = [
        SubmissionStepInline,
    ]
    readonly_fields = ["created_on", "display_merged_data"]
    actions = ["export_csv", "export_xlsx"]

    def display_merged_data(self, obj):
        merged_data = obj.get_merged_data()
        return format_html_join(
            "\n",
            "<li>{}: {}</li>",
            ((key, value) for key, value in merged_data.items()),
        )

    display_merged_data.short_description = _("Submitted data")

    def _export(self, request, queryset, file_type):
        if queryset.order_by().values("form").distinct().count() > 1:
            messages.error(
                request,
                _(
                    "Je kan alleen de inzendingen van één enkel formuliertype tegelijk exporteren."
                ),
            )
            return

        return export_submissions(queryset, file_type)

    def export_csv(self, request, queryset):
        return self._export(request, queryset, "csv")

    export_csv.short_description = _(
        "Geselecteerde %(verbose_name_plural)s exporteren als CSV-bestand."
    )

    def export_xlsx(self, request, queryset):
        return self._export(request, queryset, "xlsx")

    export_xlsx.short_description = _(
        "Geselecteerde %(verbose_name_plural)s exporteren als Excel-bestand."
    )
