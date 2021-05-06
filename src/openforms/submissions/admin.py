from django import forms
from django.contrib import admin
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
    list_display = (
        "form",
        "completed_on",
    )
    list_filter = (
        "form",
        "completed_on",
    )
    search_fields = ("form__name",)
    inlines = [
        SubmissionStepInline,
    ]
    actions = ["export"]

    def get_fields(self, request, obj=None):
        fields = ["form", "completed_on"]
        if obj:
            for key, value in obj.get_merged_data().items():
                fields.append(key)
                self.form.declared_fields.update(
                    {key: forms.CharField(initial=value, disabled=True, required=False)}
                )
        return fields

    def export(self, request, queryset):
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
        return HttpResponse(data.export("csv"), content_type="text/csv")

    export.short_description = _("Exporteren de geselecteerde submissions")
