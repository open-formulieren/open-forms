import itertools
from copy import deepcopy
from types import SimpleNamespace
from typing import List, Tuple

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


class APIPermissionTestMixin:
    full_factors = [
        ["get", "post", "put", "patch", "delete", "head", "options"],
        ["detail", "list", "create", "delete"],  # TODO more here
    ]

    def get_permissions(self) -> List[Permission]:
        try:
            return self.permissions
        except AttributeError:
            self.fail("set .permissions attribute or override .get_permissions()")

    def get_full_factors(self) -> List[List[str]]:
        extra = self.get_extra_factors()
        if not extra:
            return self.full_factors
        factors = deepcopy(self.full_factors)
        extra = set(extra)
        extra.update(factors[1])
        factors[1] = list(extra)
        return factors

    def get_extra_factors(self) -> List[List[str]]:
        try:
            return self.extra_factors
        except AttributeError:
            return []

    def extend_tests(self, base_tests, *add_test) -> List[Tuple[str, str, str]]:
        assert add_test, "pass one or more test matrices to add"
        tests = dict()
        for add in add_test:
            for method, view, res in base_tests:
                tests[(method, view)] = res
            for method, view, res in add:
                tests[(method, view)] = res
        return [(method, view, res) for (method, view), res in tests.items()]

    def assertPermission(self, permission, user, method, action, allowed):
        res = permission.has_permission(get_request(method, user), get_view(action))
        msg = (
            f"{permission} {user} {method} {action}: actual {res} != expected {allowed}"
        )
        self.assertEqual(allowed, res, msg)

    def assertPermissionStack(self, permissions, user, method, action, allowed):
        res = False
        for permission in permissions:
            # let's not shortcut the expression and invoke every permission
            res = (
                permission.has_permission(get_request(method, user), get_view(action))
                or res
            )

        p = ", ".join(map(str, permissions))
        msg = f"[{p}] {user} {method} {action}: actual {res} != expected {allowed}"
        self.assertEqual(allowed, res, msg)

    def assertPermissionMatrix(
        self,
        tests,
        user,
        full_factor_coverage=True,
        allow_unexplicit=False,
        map_head_options=False,
    ):
        if allow_unexplicit:
            assert (
                full_factor_coverage
            ), "parameter 'allow_unexplicit' requires 'full_factor_coverage'"
        if map_head_options:
            assert (
                full_factor_coverage
            ), "parameter 'map_head_options' requires 'full_factor_coverage'"

        seen = set()
        for method, action, allowed in tests:
            seen.add((method, action))

            s = "allowed" if allowed else "block"
            with self.subTest(f"{method} {action} {s}"):
                self.assertPermissionStack(
                    self.get_permissions(), user, method, action, allowed
                )

        if full_factor_coverage:
            for method, action in itertools.product(*self.full_factors):
                if (method, action) in seen:
                    continue
                if map_head_options:
                    if method in ("head", "options") and ("get", action) in seen:
                        # ideally we'd log a copy as a subtest here
                        continue

                s = "block (full check)"
                with self.subTest(f"{method} {action} {s}"):
                    # expect to fail
                    self.assertPermissionStack(
                        self.get_permissions(), user, method, action, allow_unexplicit
                    )


class FormAPIPermissionsTest(APIPermissionTestMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.permissions = [FormAPIPermissions()]

        # generic public read (here without list)
        self.public_read = [
            ("get", "detail", True),
            ("head", "detail", True),
            ("options", "detail", True),
            # custom no list
            ("get", "list", False),
            # TODO add more actions we'd always want to test even without full factors
            ("post", "create", False),
        ]

    def test_anon(self):
        tests = self.public_read
        self.assertPermissionMatrix(tests, None)

    def test_user_not_authenticated(self):
        user = AnonymousUser()
        tests = self.public_read
        self.assertPermissionMatrix(tests, user)

    def test_user_not_staff(self):
        """
        this isn't a special situation from the matrix, so defaults to public_read
        """
        user = UserFactory.create()
        self.client.force_login(user)
        tests = self.public_read
        self.assertPermissionMatrix(tests, user)

    def test_user_not_staff_with_change_permission(self):
        """
        this isn't a special situation from the matrix, so defaults to public_read
        """
        user = UserFactory.create()
        user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.client.force_login(user)
        tests = self.public_read
        self.assertPermissionMatrix(tests, user)

    def test_user_not_staff_with_view_permission(self):
        """
        token based API access to lists
        """
        user = UserFactory.create()
        user.user_permissions.add(Permission.objects.get(codename="view_form"))
        self.client.force_login(user)
        tests = self.extend_tests(
            self.public_read,
            [
                ("get", "list", True),  # needed for API access
            ],
        )
        self.assertPermissionMatrix(tests, user, map_head_options=True)

    def test_staff(self):
        """
        this isn't a special situation from the matrix, so defaults to public_read
        """
        user = StaffUserFactory.create()
        self.client.force_login(user)
        tests = self.public_read
        self.assertPermissionMatrix(tests, user)

    def test_staff_with_view_permission(self):
        """
        this isn't a special situation from the matrix, so defaults to public_read
          staff users would have 'change_form' instead of 'view_form'
        """
        user = StaffUserFactory.create()
        user.user_permissions.add(Permission.objects.get(codename="view_form"))
        self.client.force_login(user)
        tests = self.public_read
        self.assertPermissionMatrix(tests, user)

    def test_staff_with_change_permission(self):
        """
        form creators and editors
        """
        user = StaffUserFactory.create()
        user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.client.force_login(user)
        tests = self.extend_tests(
            self.public_read,
            [
                # we can do anything so overwrite our custom public_read
                ("get", "list", True),
                ("post", "create", True),
            ],
        )
        self.assertPermissionMatrix(
            tests, user, allow_unexplicit=True, map_head_options=True
        )
