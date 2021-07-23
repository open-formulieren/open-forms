from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from solo.admin import SingletonModelAdmin

from .models import GlobalConfiguration


@admin.register(GlobalConfiguration)
class GlobalConfigurationAdmin(DynamicArrayMixin, SingletonModelAdmin):
    autocomplete_fields = ("analytics_cookie_consent_group",)
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
            _("Button labels"),
            {
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
        (
            _("Analytics: Google"),
            {
                "fields": ("gtm_code", "ga_code"),
            },
        ),
        (
            _("Analytics: Matomo"),
            {
                "fields": ("matomo_url", "matomo_site_id"),
            },
        ),
        (
            _("Analytics: SiteImprove"),
            {
                "fields": ("siteimprove_id",),
            },
        ),
        (
            _("Analytics: Piwik"),
            {
                "fields": ("piwik_url", "piwik_site_id"),
            },
        ),
        (
            _("Privacy & cookies"),
            {
                "fields": ("analytics_cookie_consent_group",),
            },
        ),
        (
            _("Sessions"),
            {
                "fields": (
                    "admin_session_timeout",
                    "form_session_timeout",
                ),
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
    )
