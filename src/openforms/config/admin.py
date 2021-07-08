from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from solo.admin import SingletonModelAdmin

from .models import GlobalConfiguration


@admin.register(GlobalConfiguration)
class GlobalConfigurationAdmin(DynamicArrayMixin, SingletonModelAdmin):
    fieldsets = (
        (
            _("Confirmation email configuration"),
            {
                "fields": ("email_template_netloc_allowlist",),
            },
        ),
        (
            _("Submissions"),
            {
                "fields": ("submission_confirmation_template",),
            },
        ),
        (
            _("Feature flags & fields for testing"),
            {
                "classes": ("collapse",),
                "fields": (
                    "display_sdk_information",
                    "enable_react_form",
                    "default_test_bsn",
                    "default_test_kvk",
                    "allow_empty_initiator",
                ),
            },
        ),
        (
            _("Button Texts"),
            {
                "classes": ("collapse",),
                "fields": (
                    "form_begin_text",
                    "form_previous_text",
                    "form_change_text",
                    "form_confirm_text",
                    "form_step_previous_text",
                    "form_step_save_text",
                    "form_step_next_text",
                ),
            },
        ),
    )
