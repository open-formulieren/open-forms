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
                "fields": ("default_test_bsn", "default_test_kvk"),
            },
        ),
        (
            _("Feature flags"),
            {
                "fields": (
                    "display_sdk_information",
                    "enable_react_form",
                ),
            },
        ),
    )
