from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsStaffOrReadOnlyNoList(BasePermission):
    """
    The request is a staff user, or is a read-only request (but not for a 'list' action).
    """

    def has_permission(self, request, view):
        if request.user and request.user.is_staff:
            return True
        return request.method in SAFE_METHODS and view.action != "list"
