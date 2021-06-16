from django.contrib import admin, messages
from django.template.response import TemplateResponse
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
    readonly_fields = ["created_on"]
    actions = ["export_csv", "export_xlsx"]

    change_form_template = "openforms/submissions/templates/admin/change_form.html"

    def change_view(self, request, object_id, form_url="", extra_context=None):
        submission = self.get_object(request, object_id)
        extra_context = {
            "data": submission.data_with_component_type,
            "image_components": ["signature"],
        }
        return super().change_view(
            request,
            object_id,
            form_url,
            extra_context=extra_context,
        )

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
