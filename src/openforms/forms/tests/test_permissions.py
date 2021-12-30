from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser, Permission
from django.test import TestCase

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.forms.api.permissions import FormAPIPermissions


def get_request(method: str, user=None):
    req = SimpleNamespace()
    req.method = method.upper()
    req.user = user
    return req


def get_view(action: str):
    view = SimpleNamespace()
    view.action = action
    return view


class FormAPIPermissionsTest(TestCase):
    def setUp(self):
        super().setUp()

        self.permission = FormAPIPermissions()

        self.public_read = [
            ("get", "detail", True),
            ("get", "list", False),
            ("post", "create", False),
        ]

    def assertMultiple(self, tests, user):
        for method, action, allowed in tests:
            s = "allowed" if allowed else "block"
            with self.subTest(f"{method} {action} {s}"):
                self.assertEqual(
                    allowed,
                    self.permission.has_permission(
                        get_request(method, user), get_view(action)
                    ),
                )

    def test_anon(self):
        tests = self.public_read
        self.assertMultiple(tests, None)

    def test_user_not_authenticated(self):
        user = AnonymousUser()
        tests = self.public_read
        self.assertMultiple(tests, user)

    def test_user_not_staff(self):
        """
        this isn't a special situation from the matrix, so defaults to public_read
        """
        user = UserFactory.create()
        self.client.force_login(user)
        tests = self.public_read
        self.assertMultiple(tests, user)

    def test_user_not_staff_with_change_permission(self):
        """
        this isn't a special situation from the matrix, so defaults to public_read
        """
        user = UserFactory.create()
        user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.client.force_login(user)
        tests = self.public_read
        self.assertMultiple(tests, user)

    def test_user_not_staff_with_view_permission(self):
        """
        token based API access to lists
        """
        user = UserFactory.create()
        user.user_permissions.add(Permission.objects.get(codename="view_form"))
        self.client.force_login(user)
        tests = [
            ("get", "detail", True),
            ("get", "list", True),  # needed for API access
            ("post", "create", False),
        ]
        self.assertMultiple(tests, user)

    def test_staff(self):
        """
        this isn't a special situation from the matrix, so defaults to public_read
        """
        user = StaffUserFactory.create()
        self.client.force_login(user)
        tests = self.public_read
        self.assertMultiple(tests, user)

    def test_staff_with_view_permission(self):
        """
        this isn't a special situation from the matrix, so defaults to public_read
          staff users would have 'change_form' instead of 'view_form'
        """
        user = StaffUserFactory.create()
        user.user_permissions.add(Permission.objects.get(codename="view_form"))
        self.client.force_login(user)
        tests = self.public_read
        self.assertMultiple(tests, user)

    def test_staff_with_change_permission(self):
        """
        form creators and editors
        """
        user = StaffUserFactory.create()
        user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.client.force_login(user)
        tests = [
            ("get", "detail", True),
            ("get", "list", True),
            ("post", "create", True),
        ]
        self.assertMultiple(tests, user)
