from rest_framework.permissions import SAFE_METHODS, BasePermission


class FormAPIPermissions(BasePermission):
    """
    Custom permissions for the FormViewSet and related

    from Github issue #1000:

    1) Write access (put/patch/post/delete) is ONLY given to staff users that have forms.change_form permission
    2) Read access (get) to everything give to staff users that have form.change_form permission
    3) Read access (get) to forms.form_LIST given to non-staff users that have forms.view_form permission
    4) Read access (get) to forms.form_DETAIL given to anonymous users

    x) Anybody can detail/retrieve
    """

    def has_permission(self, request, view):
        user = request.user

        # x) anybody can read detail
        if request.method in SAFE_METHODS and view.action in ("detail", "retrieve"):
            return True

        # 4) anon users can only read detail (with above)
        elif not user or not user.is_authenticated:
            return False

        elif request.method in SAFE_METHODS:
            # 2) staff with change_form can read everything
            if user.is_staff and user.has_perm("forms.change_form"):
                return True
            # 3) non-staff with view_form can only list
            elif (
                not user.is_staff
                and view.action == "list"
                and user.has_perm("forms.view_form")
            ):
                return True
            else:
                return False
        else:
            # 1) only staff with change_form can do unsafe operations
            if user.is_staff and user.has_perm("forms.change_form"):
                return True
            else:
                return False
