from django.contrib import admin

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
