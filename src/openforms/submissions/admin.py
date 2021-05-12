from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from solo.admin import SingletonModelAdmin

from .forms import ConfirmationEmailTemplateForm
from .models import (
    ConfirmationEmailTemplate,
    SMTPServerConfig,
    Submission,
    SubmissionStep,
)
from .utils import test_conn_open


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
    readonly_fields = ("get_smtp_status",)

    def get_smtp_status(self, obj):
        smtp_config = SMTPServerConfig.get_solo()
        return test_conn_open(smtp_config)

    get_smtp_status.short_description = _("SMTP connectie status")
    get_smtp_status.boolean = True
