from rest_framework.permissions import BasePermission


class ViewFormPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm("forms.view_form")


class ViewCategoryPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm("forms.view_category")
