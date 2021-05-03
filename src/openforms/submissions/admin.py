from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .forms import ConfirmationEmailTemplateForm
from .models import (
    ConfirmationEmailTemplate,
    SMTPServerConfig,
    Submission,
    SubmissionStep,
)


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


@admin.register(ConfirmationEmailTemplate)
class ConfirmationEmailTemplateAdmin(admin.ModelAdmin):
    form = ConfirmationEmailTemplateForm


@admin.register(SMTPServerConfig)
class SMTPServerConfigAdmin(SingletonModelAdmin):
    pass
