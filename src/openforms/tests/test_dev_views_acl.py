"""
Assert that dev views are only acessible in DEBUG=True and superuser.
"""
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase, override_settings

from openforms.accounts.tests.factories import StaffUserFactory, SuperUserFactory
from openforms.emails.views import EmailWrapperTestView
from openforms.submissions.dev_views import SubmissionPDFTestView


class DevViewAccessTests(TestCase):

    dev_view_classes = (
        EmailWrapperTestView,
        SubmissionPDFTestView,
    )
    factory = RequestFactory()

    @override_settings(DEBUG=False)
    def test_no_access_with_debug_false(self):
        request = self.factory.get("/dummy")
        request.user = SuperUserFactory.create()

        for view_cls in self.dev_view_classes:
            with self.subTest(view_cls=view_cls):
                view = view_cls.as_view()

                with self.assertRaises(PermissionDenied):
                    view(request)

    @override_settings(DEBUG=True)
    def test_no_acess_if_not_superuser(self):
        request = self.factory.get("/dummy")
        request.user = StaffUserFactory.create()

        for view_cls in self.dev_view_classes:
            with self.subTest(view_cls=view_cls):
                view = view_cls.as_view()

                with self.assertRaises(PermissionDenied):
                    view(request)
