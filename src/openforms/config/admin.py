from django.contrib import admin
from django.shortcuts import resolve_url
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from import_export.admin import ImportExportModelAdmin
from modeltranslation.admin import TranslationAdmin
from solo.admin import SingletonModelAdmin

from .admin_views import ThemePreviewView
from .forms import GlobalConfigurationAdminForm, ThemeAdminForm
from .models import (
    CSPSetting,
    GlobalConfiguration,
    MapTileLayer,
    MapWMSTileLayer,
    RichTextColor,
    Theme,
)
from .resources import MapWMSTileLayerResource


@admin.register(GlobalConfiguration)
class GlobalConfigurationAdmin(TranslationAdmin, SingletonModelAdmin):
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
                    "public_reference_template",
                    "submission_confirmation_title",
                    "submission_confirmation_template",
                    "submission_report_download_link_title",
                ),
            },
        ),
        (
            _("Confirmation Email"),
            {
                "fields": ("confirmation_email_subject", "confirmation_email_content"),
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
        (
            _("Submissions with cosigning"),
            {
                "fields": (
                    "cosign_submission_confirmation_title",
                    "cosign_submission_confirmation_template",
                ),
            },
        ),
        (
            _("Co-sign emails"),
            {
                "fields": (
                    "cosign_request_template",
                    "cosign_confirmation_email_subject",
                    "cosign_confirmation_email_content",
                ),
            },
        ),
        (
            _("Email address verification emails"),
            {
                "fields": (
                    "email_verification_request_subject",
                    "email_verification_request_content",
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
                    "main_website",
                    "favicon",
                    "default_theme",
                    "organization_oin",
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
        (
            _("Plugin configuration"),
            {
                "fields": (
                    "plugin_configuration",
                    "family_members_data_api",
                    "communication_preferences_portal_url",
                    "reference_lists_services",
                )
            },
        ),
        (
            _("Registration"),
            {
                "fields": (
                    "registration_attempt_limit",
                    "wait_for_payment_to_register",
                    "allow_empty_initiator",
                )
            },
        ),
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
            _("Payments"),
            {
                "fields": ("payment_order_id_template",),
            },
        ),
        (
            _("Feature flags & fields for testing"),
            {
                "classes": ("collapse",),
                "fields": ("feature_flags_link",),
            },
        ),
    )
    readonly_fields = ("feature_flags_link",)
    filter_horizontal = ("reference_lists_services",)

    @admin.display(description=_("feature flags"))
    def feature_flags_link(self, obj) -> str:
        return format_html(
            '<a href="{}">{}</a>',
            reverse("admin:flags_flagstate_changelist"),
            _("Manage"),
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


@admin.register(MapTileLayer)
class MapTileLayerAdmin(admin.ModelAdmin):
    fields = (
        "label",
        "identifier",
        "url",
    )
    list_display = (
        "label",
        "identifier",
        "url",
    )
    prepopulated_fields = {"identifier": ("label",)}


@admin.register(MapWMSTileLayer)
class MapWMSTileLayerAdmin(ImportExportModelAdmin):
    list_display = ("name", "url", "uuid")
    search_fields = ("name", "uuid")

    # Import and export options:
    resource_classes = (MapWMSTileLayerResource,)


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


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ("name", "logo", "email_logo", "classname", "get_preview_url")
    search_fields = ("name", "classname")

    form = ThemeAdminForm
    fieldsets = (
        (None, {"fields": ("name",)}),
        (
            _("Organization configuration"),
            {"fields": ("organization_name", "main_website", "favicon")},
        ),
        (_("Logo"), {"fields": ("logo", "email_logo")}),
        (
            _("Appearance"),
            {
                "fields": (
                    "classname",
                    "stylesheet",
                    "stylesheet_file",
                    "design_token_values",
                )
            },
        ),
    )

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "<path:object_id>/preview/",
                self.admin_site.admin_view(ThemePreviewView.as_view()),
                name="config_preview_theme",
            ),
        ]
        return my_urls + urls

    @admin.display(description=_("Preview"))
    def get_preview_url(self, obj: Theme) -> str:
        path = resolve_url("admin:config_preview_theme", object_id=obj.pk)
        return format_html('<a href="{}">{}</a>', path, _("Show preview"))
