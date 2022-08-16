from django import forms
from django.contrib import admin

from .models import AuthInfo


class AuthInfoAdminForm(forms.ModelForm):
    class Meta:
        model = AuthInfo
        fields = (
            "plugin",
            "attribute",
            "value",
            "submission",
            "machtigen",
            "attribute_hashed",
        )
        widgets = {
            "machtigen": forms.Textarea(attrs={"cols": 20, "rows": 1}),
            "plugin": forms.TextInput(attrs={"size": 20}),
            "value": forms.TextInput(attrs={"size": 20}),
        }


class AuthInfoInline(admin.TabularInline):
    model = AuthInfo
    extra = 0
    form = AuthInfoAdminForm

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AuthInfo)
class AuthInfoAdmin(admin.ModelAdmin):
    list_display = ("submission", "plugin", "attribute")
    list_filter = ("plugin", "attribute")
    search_fields = ("submission__pk",)
    raw_id_fields = ("submission",)
