from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from modeltranslation.admin import TranslationAdmin
from solo.admin import SingletonModelAdmin

from .forms import GlobalConfigurationAdminForm
from .models import CSPSetting, GlobalConfiguration, RichTextColor


@admin.register(GlobalConfiguration)
class GlobalConfigurationAdmin(
    DynamicArrayMixin, TranslationAdmin, SingletonModelAdmin
):
    form = GlobalConfigurationAdminForm
    fieldsets = (
        (
            _("Email security configuration"),
            {
                "fields": ("email_template_netloc_allowlist",),
            },
        ),
        (
            _("Submissions"),
            {
                "fields": (
                    "submission_confirmation_template",
                    "submission_report_download_link_title",
                ),
            },
        ),
        (
            _("Confirmation Email"),
            {
                "fields": (
                    "confirmation_email_subject",
                    "confirmation_email_content",
                    "show_form_link_in_cosign_email",
                ),
            },
        ),
        (
            _("Save Form Email"),
            {
                "fields": (
                    "save_form_email_subject",
                    "save_form_email_content",
                ),
            },
        ),
        (_("General Email settings"), {"fields": ("recipients_email_digest",)}),
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
            _("General form options"),
            {
                "fields": (
                    "form_fields_required_default",
                    "form_display_required_with_asterisk",
                    "form_upload_default_file_types",
                    "hide_non_applicable_steps",
                    (
                        "form_map_default_zoom_level",
                        "form_map_default_latitude",
                        "form_map_default_longitude",
                    ),
                )
            },
        ),
        (
            _("Organization configuration"),
            {
                "fields": (
                    "organization_name",
                    "logo",
                    "main_website",
                    "favicon",
                    "theme_classname",
                    "theme_stylesheet",
                    "theme_stylesheet_file",
                    "design_token_values",
                ),
            },
        ),
        (
            _("Statement of truth"),
            {
                "fields": (
                    "ask_statement_of_truth",
                    "statement_of_truth_label",
                ),
            },
        ),
        (
            _("Privacy"),
            {
                "fields": (
                    "ask_privacy_consent",
                    "privacy_policy_url",
                    "privacy_policy_label",
                ),
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
            _("Data removal"),
            {
                "fields": (
                    "successful_submissions_removal_limit",
                    "successful_submissions_removal_method",
                    "incomplete_submissions_removal_limit",
                    "incomplete_submissions_removal_method",
                    "errored_submissions_removal_limit",
                    "errored_submissions_removal_method",
                    "all_submissions_removal_limit",
                ),
            },
        ),
        (_("Search engines"), {"fields": ("allow_indexing_form_detail",)}),
        (_("Plugin configuration"), {"fields": ("plugin_configuration",)}),
        (_("Registration"), {"fields": ("registration_attempt_limit",)}),
        (
            _("Virus scan"),
            {
                "fields": (
                    "enable_virus_scan",
                    "clamav_host",
                    "clamav_port",
                    "clamav_timeout",
                )
            },
        ),
        (
            _("Feature flags & fields for testing"),
            {
                "classes": ("collapse",),
                "fields": (
                    "display_sdk_information",
                    "enable_demo_plugins",
                    "enable_react_formio_builder",
                    "allow_empty_initiator",
                    "payment_order_id_prefix",
                ),
            },
        ),
    )


@admin.register(RichTextColor)
class RichTextColorAdmin(admin.ModelAdmin):
    fields = [
        "label",
        "color",
    ]
    list_display = [
        "label",
        "example",
        "color",
    ]


@admin.register(CSPSetting)
class CSPSettingAdmin(admin.ModelAdmin):
    readonly_fields = ("content_type_link",)
    fields = [
        "directive",
        "value",
        "identifier",
        "content_type_link",
    ]
    list_display = [
        "directive",
        "value",
        "identifier",
    ]
    list_filter = [
        "directive",
        "identifier",
    ]
    search_fields = [
        "directive",
        "value",
        "identifier",
    ]

    def content_type_link(self, obj):
        ct = obj.content_type
        url = reverse(f"admin:{ct.app_label}_{ct.model}_change", args=(obj.object_id,))
        link = format_html('<a href="{u}">{t}</a>', u=url, t=str(obj.content_object))
        return link

    content_type_link.short_description = _("Content type")
