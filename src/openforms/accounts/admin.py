from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from .models import User


def _append_field_to_fieldsets(fieldsets, set_name, *field_names):
    for fset in fieldsets:
        if fset[0] == set_name:
            fset[1]["fields"] = fset[1]["fields"] + field_names
            return
    raise Exception(f"cannot find fieldset {set_name}")


@admin.register(User)
class _UserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + (
        "employee_id",
        "is_superuser",
        "get_groups",
    )
    search_fields = UserAdmin.search_fields + ("employee_id",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("groups")

    def get_groups(self, obj):
        return list(obj.groups.all())

    get_groups.short_description = _("Groups")


_append_field_to_fieldsets(_UserAdmin.fieldsets, _("Personal info"), "employee_id")
