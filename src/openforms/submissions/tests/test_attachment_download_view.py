from django.test import override_settings
from django.urls import reverse

from django_webtest import WebTest
from furl import furl
from privates.test import temp_private_root

from openforms.accounts.tests.factories import (
    StaffUserFactory,
    SuperUserFactory,
    UserFactory,
)
from openforms.utils.tests.auth_assert import AuthAssertMixin

from .factories import SubmissionFileAttachmentFactory


@override_settings(SENDFILE_BACKEND="django_sendfile.backends.nginx")
@temp_private_root()
class SubmissionAttachmentDownloadTest(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.super_user = (
            SuperUserFactory.create()
        )  # user with all permissions, tests non-permission related behaviour

    def test_incomplete_submission_404(self):
        submission_file_attachment = SubmissionFileAttachmentFactory.create(
            submission_step__submission__completed=False,
        )
        path = reverse(
            "submissions:attachment-download",
            kwargs={"uuid": submission_file_attachment.uuid},
        )
        url = furl(path).add({"hash": "dummy-hash"})

        response = self.app.get(url, user=self.super_user, status=404)

        self.assertEqual(response.status_code, 404)

    def test_submission_not_registered_yet_404(self):
        submission_file_attachments = [
            SubmissionFileAttachmentFactory.create(
                submission_step__submission__completed=True,
                submission_step__submission__registration_failed=True,
            ),
            SubmissionFileAttachmentFactory.create(
                submission_step__submission__completed=True,
                submission_step__submission__registration_pending=True,
            ),
            SubmissionFileAttachmentFactory.create(
                submission_step__submission__completed=True,
                submission_step__submission__registration_in_progress=True,
            ),
        ]

        for submission_file_attachment in submission_file_attachments:
            with self.subTest(submission_file_attachment):
                path = reverse(
                    "submissions:attachment-download",
                    kwargs={"uuid": submission_file_attachment.uuid},
                )
                url = furl(path).add({"hash": "dummy-hash"})

                response = self.app.get(url, user=self.super_user, status=404)

                self.assertEqual(response.status_code, 404)

    def test_valid_preconditions_missing_hash_403(self):
        submission_file_attachment = SubmissionFileAttachmentFactory.create(
            submission_step__submission__completed=True,
            submission_step__submission__registration_success=True,
        )
        path = reverse(
            "submissions:attachment-download",
            kwargs={"uuid": submission_file_attachment.uuid},
        )

        response = self.app.get(path, user=self.super_user, status=403)

        self.assertEqual(response.status_code, 403)

    def test_valid_preconditions_invalid_hash_403(self):
        submission_file_attachment = SubmissionFileAttachmentFactory.create(
            submission_step__submission__completed=True,
            submission_step__submission__registration_success=True,
        )
        path = reverse(
            "submissions:attachment-download",
            kwargs={"uuid": submission_file_attachment.uuid},
        )
        url = furl(path).add({"hash": "badhash"})

        response = self.app.get(url, user=self.super_user, status=403)

        self.assertEqual(response.status_code, 403)

    def test_nginx_sendfile_response(self):
        submission_file_attachment = SubmissionFileAttachmentFactory.create(
            submission_step__submission__completed=True,
            submission_step__submission__registration_success=True,
        )
        path = reverse(
            "submissions:attachment-download",
            kwargs={"uuid": submission_file_attachment.uuid},
        )
        url = furl(path).add({"hash": submission_file_attachment.content_hash})

        response = self.app.get(url, user=self.super_user)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Content-Disposition", response.headers)
        self.assertEqual(
            response.headers["Content-Disposition"],
            f'attachment; filename="{submission_file_attachment.get_display_name()}"',
        )

        self.assertIn("X-Accel-Redirect", response.headers)


@temp_private_root()
class PermissionTests(AuthAssertMixin, WebTest):
    def test_not_authenticated(self):
        submission_file_attachment = SubmissionFileAttachmentFactory.create(
            submission_step__submission__completed=True,
            submission_step__submission__registration_success=True,
        )
        path = reverse(
            "submissions:attachment-download",
            kwargs={"uuid": submission_file_attachment.uuid},
        )
        url = furl(path).add({"hash": submission_file_attachment.content_hash})

        response = self.app.get(url)

        self.assertLoginRequired(response, url)

    def test_insufficient_permissions(self):
        submission_file_attachment = SubmissionFileAttachmentFactory.create(
            submission_step__submission__completed=True,
            submission_step__submission__registration_success=True,
        )
        path = reverse(
            "submissions:attachment-download",
            kwargs={"uuid": submission_file_attachment.uuid},
        )
        url = furl(path).add({"hash": submission_file_attachment.content_hash})

        bad_users = [
            UserFactory.create(),
            UserFactory.create(
                user_permissions=["submissions.view_submissionfileattachment"]
            ),
            StaffUserFactory.create(),
        ]

        for user in bad_users:
            with self.subTest(
                is_staff=user.is_staff,
                is_superuser=user.is_superuser,
                permissions=user.user_permissions.all(),
            ):
                response = self.app.get(url, user=user, status=403)

                self.assertEqual(response.status_code, 403)

    def test_sufficient_permissions(self):
        user = StaffUserFactory.create(
            user_permissions=["submissions.view_submissionfileattachment"]
        )
        submission_file_attachment = SubmissionFileAttachmentFactory.create(
            submission_step__submission__completed=True,
            submission_step__submission__registration_success=True,
        )
        path = reverse(
            "submissions:attachment-download",
            kwargs={"uuid": submission_file_attachment.uuid},
        )
        url = furl(path).add({"hash": submission_file_attachment.content_hash})

        response = self.app.get(url, user=user)

        self.assertEqual(response.status_code, 200)
