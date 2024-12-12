from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import AuthInfo, RegistratorInfo


class AuthInfoAdminForm(forms.ModelForm):
    class Meta:
        model = AuthInfo
        fields = (
            "plugin",
            "attribute",
            "value",
            "submission",
            "loa",
            "acting_subject_identifier_type",
            "acting_subject_identifier_value",
            "legal_subject_identifier_type",
            "legal_subject_identifier_value",
            "legal_subject_service_restriction",
            "mandate_context",
            "attribute_hashed",
        )
        widgets = {
            "plugin": forms.TextInput(attrs={"size": 20}),
            "value": forms.TextInput(attrs={"size": 20}),
        }


class AuthInfoInline(admin.StackedInline):
    """
    Display authentication information inline.

    There can only ever  be a single :class:`AuthInfo` instance related to a submission,
    so a stacked inline with fieldsets makes more sense than a tabular inline.
    """

    model = AuthInfo
    extra = 0
    form = AuthInfoAdminForm
    fieldsets = (
        (
            None,
            {
                "fields": (
                    (
                        "submission",
                        "attribute",
                        "value",
                    ),
                )
            },
        ),
        (
            _("Means"),
            {"fields": ("plugin", "loa"), "classes": ("collapse",)},
        ),
        (
            _("Acting subject"),
            {
                "fields": (
                    "acting_subject_identifier_type",
                    "acting_subject_identifier_value",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Legal subject"),
            {
                "fields": (
                    "legal_subject_identifier_type",
                    "legal_subject_identifier_value",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Mandate"),
            {
                "fields": ("mandate_context",),
                "classes": ("collapse",),
            },
        ),
        (
            _("Misc"),
            {"fields": ("attribute_hashed",), "classes": ("collapse in",)},
        ),
    )

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AuthInfo)
class AuthInfoAdmin(admin.ModelAdmin):
    list_display = ("submission", "plugin", "attribute", "loa")
    list_filter = ("plugin", "attribute")
    search_fields = ("submission__pk",)
    raw_id_fields = ("submission",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "submission",
                    "attribute",
                    "value",
                )
            },
        ),
        (
            _("Means"),
            {"fields": ("plugin", "loa")},
        ),
        (
            _("Acting subject"),
            {
                "fields": (
                    "acting_subject_identifier_type",
                    "acting_subject_identifier_value",
                )
            },
        ),
        (
            _("Legal subject"),
            {
                "fields": (
                    "legal_subject_identifier_type",
                    "legal_subject_identifier_value",
                )
            },
        ),
        (_("Mandate"), {"fields": ("mandate_context",)}),
        (
            _("Misc"),
            {"fields": ("attribute_hashed",), "classes": ("collapse in",)},
        ),
    )


class RegistratorInfoAdminForm(forms.ModelForm):
    class Meta:
        model = RegistratorInfo
        fields = (
            "plugin",
            "attribute",
            "value",
            "submission",
            "attribute_hashed",
        )
        widgets = {
            "plugin": forms.TextInput(attrs={"size": 20}),
            "value": forms.TextInput(attrs={"size": 20}),
        }


class RegistratorInfoInline(admin.TabularInline):
    model = RegistratorInfo
    extra = 0
    form = RegistratorInfoAdminForm

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RegistratorInfo)
class RegistratorInfoAdmin(admin.ModelAdmin):
    list_display = ("submission", "plugin", "attribute")
    list_filter = ("plugin", "attribute")
    search_fields = ("submission__pk",)
    raw_id_fields = ("submission",)
