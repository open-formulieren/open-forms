from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from hijack_admin.admin import HijackUserAdminMixin

from .models import User


@admin.register(User)
class _UserAdmin(UserAdmin, HijackUserAdminMixin):
    list_display = UserAdmin.list_display + (
        "is_superuser",
        "get_groups",
        "hijack_field",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('groups')
