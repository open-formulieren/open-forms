from django.contrib import admin, messages
from django.utils.html import format_html, format_html_join
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
        "registration_status",
        "created_on",
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

        regular_values = []
        image_values = []
        for key, value in merged_data.items():
            if "data:image/png" not in str(value):
                regular_values.append((key, value))
            else:
                image_values.append((key, value))

        ret = format_html_join(
            "\n",
            "<li>{}: {}</li>",
            ((key, value) for key, value in regular_values),
        )
        ret += format_html_join(
            "\n",
            "<li>{}: <br><img style='width:350px' src='{}' alt='{}'></li>",
            ((key, value, key) for key, value in image_values),
        )
        return format_html("<ul>{}</ul>", ret)

    display_merged_data.short_description = _("Submitted data")

    def _export(self, request, queryset, file_type):
        if queryset.order_by().values("form").distinct().count() > 1:
            messages.error(
                request,
                _("You can only export the submissions of the same form type."),
            )
            return

        return export_submissions(queryset, file_type)

    def export_csv(self, request, queryset):
        return self._export(request, queryset, "csv")

    export_csv.short_description = _(
        "Export selected %(verbose_name_plural)s as CSV-file."
    )

    def export_xlsx(self, request, queryset):
        return self._export(request, queryset, "xlsx")

    export_xlsx.short_description = _(
        "Export selected %(verbose_name_plural)s as Excel-file."
    )
