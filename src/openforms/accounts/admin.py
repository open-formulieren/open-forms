from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from .models import User


@admin.register(User)
class _UserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + (
        "is_superuser",
        "get_groups",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("groups")

    def get_groups(self, obj):
        return list(obj.groups.all())

    get_groups.short_description = _("Groups")
