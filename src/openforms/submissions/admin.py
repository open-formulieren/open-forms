import tablib
from django.contrib import admin
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

from .models import Submission, SubmissionStep


class SubmissionStepInline(admin.StackedInline):
    model = SubmissionStep
    extra = 0


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "form",
        "completed_on",
    )
    list_filter = ("form", "completed_on",)
    search_fields = ("form__name",)
    inlines = [
        SubmissionStepInline,
    ]
    actions = ['export']

    def export(self, request, queryset):
        data = tablib.Dataset(headers=['Formuliernaam', 'Inzendingdatum'])
        for submission in queryset:
            data.append([submission.form.name, submission.completed_on])
        return HttpResponse(data.export('csv'), content_type='text/csv')
    export.short_description = _("Exporteren de geselecteerde submissions")
