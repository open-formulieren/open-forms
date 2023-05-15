from unittest.mock import patch

from django.http import HttpRequest
from django.test import TestCase, override_settings
from django.urls import reverse

from furl import furl

from openforms.accounts.tests.factories import UserFactory
from openforms.authentication.constants import FORM_AUTH_SESSION_KEY
from openforms.submissions.tests.factories import SubmissionFactory


class SearchSubmissionForCosignView(TestCase):
    def test_successfully_get_form(self):
        SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                    "authPlugin": "digid",
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
            completed=True,
            cosign_complete=False,
            form__slug="form-to-cosign",
        )
        user = UserFactory.create()
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
        }
        session.save()

        find_submission_page = furl(
            reverse(
                "submissions:find-submission-for-cosign",
                kwargs={"form_slug": "form-to-cosign"},
            )
        )
        find_submission_page.args.set("next", "http://openforms.nl/form-slug/cosign")

        self.client.login(
            request=HttpRequest(), username=user.username, password=user.password
        )
        with patch("openforms.submissions.views.allow_redirect_url", return_value=True):
            response = self.client.get(find_submission_page)

        self.assertEqual(response.status_code, 200)

    def test_submit_form_redirects_to_cosign_page(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                    "authPlugin": "digid",
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
            completed=True,
            public_registration_reference="OF-123456",
            cosign_complete=False,
            form__slug="form-to-cosign",
        )
        user = UserFactory.create()
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
        }
        session.save()

        next_url = "http://openforms.nl/form-slug/cosign"
        find_submission_page = furl(
            reverse(
                "submissions:find-submission-for-cosign",
                kwargs={"form_slug": "form-to-cosign"},
            )
        )
        find_submission_page.args.set("next", next_url)

        self.client.login(
            request=HttpRequest(), username=user.username, password=user.password
        )
        with patch("openforms.submissions.views.allow_redirect_url", return_value=True):
            response = self.client.post(
                find_submission_page,
                data={"code": submission.public_registration_reference},
            )

        self.assertRedirects(response, next_url, fetch_redirect_response=False)

    def test_user_has_authenticated_with_wrong_plugin(self):
        SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                    "authPlugin": "digid",
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
            completed=True,
            cosign_complete=False,
            form__slug="form-to-cosign",
        )
        user = UserFactory.create()
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "wrong-plugin",
            "attribute": "bsn",
            "value": "123456782",
        }
        session.save()

        find_submission_page = furl(
            reverse(
                "submissions:find-submission-for-cosign",
                kwargs={"form_slug": "form-to-cosign"},
            )
        )
        find_submission_page.args.set("next", "http://openforms.nl/form-slug/cosign")

        self.client.login(
            request=HttpRequest(), username=user.username, password=user.password
        )
        with patch("openforms.submissions.views.allow_redirect_url", return_value=True):
            response = self.client.get(find_submission_page)

        self.assertEqual(response.status_code, 403)

    def test_wrong_form_slug_gives_error(self):
        SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                    "authPlugin": "digid",
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
            completed=True,
            cosign_complete=False,
            form__slug="form-to-cosign",
        )
        user = UserFactory.create()
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
        }
        session.save()

        find_submission_page = furl(
            reverse(
                "submissions:find-submission-for-cosign",
                kwargs={"form_slug": "wrong-slug"},
            )
        )
        find_submission_page.args.set("next", "http://openforms.nl/form-slug/cosign")

        self.client.login(
            request=HttpRequest(), username=user.username, password=user.password
        )
        with patch("openforms.submissions.views.allow_redirect_url", return_value=True):
            response = self.client.get(find_submission_page)

        self.assertEqual(response.status_code, 404)

    @override_settings(LANGUAGE_CODE="en")
    def test_wrong_submission_reference_gives_error(self):
        SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                    "authPlugin": "digid",
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
            completed=True,
            public_registration_reference="OF-123456",
            cosign_complete=False,
            form__slug="form-to-cosign",
        )
        user = UserFactory.create()
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
        }
        session.save()

        next_url = "http://openforms.nl/form-slug/cosign"
        find_submission_page = furl(
            reverse(
                "submissions:find-submission-for-cosign",
                kwargs={"form_slug": "form-to-cosign"},
            )
        )
        find_submission_page.args.set("next", next_url)

        self.client.login(
            request=HttpRequest(), username=user.username, password=user.password
        )
        with patch("openforms.submissions.views.allow_redirect_url", return_value=True):
            response = self.client.post(
                find_submission_page,
                data={"code": "WRONG-REFERENCE"},
            )

        self.assertEqual(response.status_code, 200)  # does not redirect
        self.assertIn(
            b"Could not find submission corresponding to this code that requires co-signing",
            response.content,
        )

    def test_submission_already_cosigned_raises_error(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                    "authPlugin": "digid",
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
            completed=True,
            public_registration_reference="OF-123456",
            cosign_complete=True,  # Already co-signed
            form__slug="form-to-cosign",
        )
        user = UserFactory.create()
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
        }
        session.save()

        next_url = "http://openforms.nl/form-slug/cosign"
        find_submission_page = furl(
            reverse(
                "submissions:find-submission-for-cosign",
                kwargs={"form_slug": "form-to-cosign"},
            )
        )
        find_submission_page.args.set("next", next_url)

        self.client.login(
            request=HttpRequest(), username=user.username, password=user.password
        )
        with patch("openforms.submissions.views.allow_redirect_url", return_value=True):
            response = self.client.post(
                find_submission_page,
                data={"code": submission.public_registration_reference},
            )

        self.assertEqual(response.status_code, 200)  # does not redirect
        self.assertIn(
            b"Could not find submission corresponding to this code that requires co-signing",
            response.content,
        )

    @override_settings(LANGUAGE_CODE="en")
    def test_missing_next_url_gives_error(self):
        SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                    "authPlugin": "digid",
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
            completed=True,
            cosign_complete=False,
            form__slug="form-to-cosign",
        )
        user = UserFactory.create()
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
        }
        session.save()

        find_submission_page = furl(
            reverse(
                "submissions:find-submission-for-cosign",
                kwargs={"form_slug": "form-to-cosign"},
            )
        )
        # find_submission_page.args.set("next", "http://openforms.nl/form-slug/cosign") # <== No next arg added

        self.client.login(
            request=HttpRequest(), username=user.username, password=user.password
        )
        with patch("openforms.submissions.views.allow_redirect_url", return_value=True):
            response = self.client.get(find_submission_page)

        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Missing or not allowed url for co-signing", response.content)

    @override_settings(LANGUAGE_CODE="en")
    def test_redirect_must_be_to_allowed_url(self):
        SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                    "authPlugin": "digid",
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
            completed=True,
            cosign_complete=False,
            form__slug="form-to-cosign",
        )
        user = UserFactory.create()
        session = self.client.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
        }
        session.save()

        find_submission_page = furl(
            reverse(
                "submissions:find-submission-for-cosign",
                kwargs={"form_slug": "form-to-cosign"},
            )
        )
        find_submission_page.args.set("next", "http://openforms.nl/form-slug/cosign")

        self.client.login(
            request=HttpRequest(), username=user.username, password=user.password
        )
        with patch(
            "openforms.submissions.views.allow_redirect_url", return_value=False
        ):
            response = self.client.get(find_submission_page)

        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Missing or not allowed url for co-signing", response.content)
