class PermissionFilterMixin:
    """
    Call filter_queryset method of the permission class, if it exists.
    """

    def filter_queryset(self, queryset):
        for permission in self.get_permissions():
            if not hasattr(permission, "filter_queryset"):
                continue
            queryset = permission.filter_queryset(self.request, self, queryset)
        return super().filter_queryset(queryset)
