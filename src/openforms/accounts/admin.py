from functools import update_wrapper
from typing import Literal

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from django.urls import path
from django.utils.translation import gettext_lazy as _

from .forms import UserPreferencesForm
from .models import User, UserPreferences


def _append_field_to_fieldsets(fieldsets, set_name, *field_names):
    for fset in fieldsets:
        if fset[0] == set_name:
            fset[1]["fields"] = fset[1]["fields"] + field_names
            return
    raise Exception(f"cannot find fieldset {set_name}")  # pragma: no cover


@admin.register(User)
class _UserAdmin(UserAdmin):
    list_display = tuple(UserAdmin.list_display) + (  # pyright: ignore[reportGeneralTypeIssues]
        "employee_id",
        "is_superuser",
        "get_groups",
    )
    search_fields = tuple(UserAdmin.search_fields) + ("employee_id",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("groups")

    @admin.display(description=_("Groups"))
    def get_groups(self, obj):
        return list(obj.groups.all())


_append_field_to_fieldsets(_UserAdmin.fieldsets, _("Personal info"), "employee_id")


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    form = UserPreferencesForm
    save_as_continue = False

    # method overrides are inspired by django-solo

    def has_module_permission(self, request) -> Literal[True]:
        """
        Always give module permissions.

        Users should always have permission to update their own preferences, which
        requires at least the module permission.
        """
        return True

    def has_change_permission(self, request, obj=None) -> Literal[True]:
        """
        Always give change permission.

        Users should always have permission to update their own preferences, which
        requires at least the module permission. The URL routing guards against updating
        other people's preferences.
        """
        return True

    def has_add_permission(self, request: HttpRequest):
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None):
        return False

    def get_urls(self):
        urls = super().get_urls()

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            wrapper.model_admin = self  # pyright: ignore[reportFunctionMemberAccess]
            return update_wrapper(wrapper, view)

        url_name_prefix = f"{self.model._meta.app_label}_{self.model._meta.model_name}"
        custom_urls = [
            path(
                "",
                wrap(self.change_view),
                {"object_id": "dummy"},
                name=f"{url_name_prefix}_change",
            ),
        ]
        return custom_urls + urls

    def change_view(
        self,
        request: HttpRequest,
        object_id: str,
        form_url: str = "",
        extra_context: dict | None = None,
    ):
        # discard object_id input, always use own user object. Admins can still edit
        # other people via the regular user admin.
        _object_id = str(request.user.pk)

        # detect tampering with URLs
        if object_id != "dummy" and object_id != _object_id:
            raise PermissionDenied()

        extra_context = extra_context or {}
        extra_context["show_save_and_continue"] = False
        return super().change_view(
            request, _object_id, form_url=form_url, extra_context=extra_context
        )
