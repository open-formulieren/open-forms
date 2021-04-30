from django.contrib import admin

from .models import Submission, SubmissionStep


class SubmissionStepInline(admin.StackedInline):
    model = SubmissionStep
    extra = 0


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "created_on",
        "form",
        "registration_status",
    )
    list_filter = ("form",)
    inlines = [
        SubmissionStepInline,
    ]
