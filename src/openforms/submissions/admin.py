from django import forms
from django.contrib import admin, messages
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

import tablib

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
    actions = ["export_csv", "export_xls"]

    def get_fields(self, request, obj=None):
        fields = ["form", "completed_on"]
        if obj:
            for key, value in obj.get_merged_data().items():
                fields.append(key)
                self.form.declared_fields.update(
                    {key: forms.CharField(initial=value, disabled=True, required=False)}
                )
        return fields

    def _export(self, request, queryset, file_type):
        file_type_to_content_type = {
            "csv": "text/csv",
            "xls": "application/vnd.ms-excel",
        }

        if queryset.order_by().values("form").distinct().count() > 1:
            messages.error(
                request,
                _("Mag alleen de Submissions van een Form op een keer exporten"),
            )
            return

        headers = []
        for submission in queryset:
            headers += list(submission.get_merged_data().keys())
        headers = list(dict.fromkeys(headers))  # Remove duplicates
        data = tablib.Dataset(headers=["Formuliernaam", "Inzendingdatum"] + headers)
        for submission in queryset:
            submission_data = [submission.form.name, submission.completed_on]
            merged_data = submission.get_merged_data()
            for header in headers:
                submission_data.append(merged_data.get(header))
            data.append(submission_data)
        return HttpResponse(
            data.export(file_type), content_type=file_type_to_content_type[file_type]
        )

    def export_csv(self, request, queryset):
        return self._export(request, queryset, "csv")

    export_csv.short_description = _(
        "Exporteren de geselecteerde Submissions als een csv file"
    )

    def export_xls(self, request, queryset):
        return self._export(request, queryset, "xls")

    export_xls.short_description = _(
        "Exporteren de geselecteerde Submissions als een xls file"
    )
