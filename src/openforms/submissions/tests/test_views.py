from django.contrib.sessions.backends.base import SessionBase
from django.core.cache import cache
from django.test import override_settings, tag
from django.urls import reverse
from django.utils.translation import gettext as _

from django_webtest import WebTest

from openforms.authentication.constants import FORM_AUTH_SESSION_KEY
from openforms.authentication.contrib.digid.constants import DIGID_DEFAULT_LOA
from openforms.frontend.tests import FrontendRedirectMixin
from openforms.submissions.tests.factories import SubmissionFactory


class SearchSubmissionForCosignView(FrontendRedirectMixin, WebTest):
    def setUp(self) -> None:
        super().setUp()

        # Needed so that when we get self.app.session we get a session object and not a dict
        self.app.get("/", status=403)

    def test_successfully_submit_form(self):
        submission = SubmissionFactory.from_components(
            form__authentication_backend="digid",
            form__authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
            completed=True,
            cosign_complete=False,
            form__slug="form-to-cosign",
            form_url="http://url-to-form.nl/startpagina",
            public_registration_reference="OF-IMAREFERENCE",
        )
        session = self.app.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
            "loa": DIGID_DEFAULT_LOA,
        }
        session.save()

        response = self.app.get(
            reverse(
                "submissions:find-submission-for-cosign",
                kwargs={"form_slug": "form-to-cosign"},
            )
        )

        form = response.forms[0]
        form["code"] = submission.public_registration_reference
        submission_response = form.submit()

        self.assertRedirectsToFrontend(
            submission_response,
            frontend_base_url="http://url-to-form.nl/",
            action="cosign",
            action_params={
                "submission_uuid": str(submission.uuid),
            },
            fetch_redirect_response=False,
        )

    def test_successfully_resolve_code_from_GET_params(self):
        submission = SubmissionFactory.from_components(
            form__authentication_backend="digid",
            form__authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
            completed=True,
            cosign_complete=False,
            form__slug="form-to-cosign",
            form_url="http://url-to-form.nl/startpagina",
            public_registration_reference="OF-IMAREFERENCE",
        )
        session = self.app.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
            "loa": DIGID_DEFAULT_LOA,
        }
        session.save()

        response = self.app.get(
            reverse(
                "submissions:find-submission-for-cosign",
                kwargs={"form_slug": "form-to-cosign"},
            ),
            {"code": submission.public_registration_reference},
        )

        self.assertRedirectsToFrontend(
            response,
            frontend_base_url="http://url-to-form.nl/",
            action="cosign",
            action_params={
                "submission_uuid": str(submission.uuid),
            },
            fetch_redirect_response=False,
        )

    def test_user_no_auth_details_in_session(self):
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
            form_url="http://url-to-form.nl/startpagina",
        )
        self.app.get(
            reverse(
                "submissions:find-submission-for-cosign",
                kwargs={"form_slug": "form-to-cosign"},
            ),
            status=403,
        )

    def test_user_has_authenticated_with_wrong_plugin(self):
        SubmissionFactory.from_components(
            form__authentication_backend="digid",
            form__authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
            completed=True,
            cosign_complete=False,
            form__slug="form-to-cosign",
            form_url="http://url-to-form.nl/startpagina",
        )

        session = self.app.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "not-digid",
            "attribute": "bsn",
            "value": "123456782",
        }
        session.save()

        self.app.get(
            reverse(
                "submissions:find-submission-for-cosign",
                kwargs={"form_slug": "form-to-cosign"},
            ),
            status=403,
        )

    def test_wrong_form_slug_gives_error(self):
        SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
            completed=True,
            cosign_complete=False,
            form__slug="form-to-cosign",
            form_url="http://url-to-form.nl/startpagina",
        )
        session = self.app.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
            "loa": DIGID_DEFAULT_LOA,
        }
        session.save()

        self.app.get(
            reverse(
                "submissions:find-submission-for-cosign",
                kwargs={"form_slug": "wrong-slug"},
            ),
            status=404,
        )

    @override_settings(LANGUAGE_CODE="en")
    def test_wrong_submission_reference_gives_error(self):
        SubmissionFactory.from_components(
            form__authentication_backend="digid",
            form__authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
            completed=True,
            public_registration_reference="OF-123456",
            cosign_complete=False,
            form__slug="form-to-cosign",
            form_url="http://url-to-form.nl/startpagina",
        )
        session = self.app.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
            "loa": DIGID_DEFAULT_LOA,
        }
        session.save()

        response = self.app.get(
            reverse(
                "submissions:find-submission-for-cosign",
                kwargs={"form_slug": "form-to-cosign"},
            )
        )

        form = response.forms[0]
        form["code"] = "WRONG-REFERENCE"
        submission_response = form.submit()

        self.assertEqual(200, submission_response.status_code)

        error_node = submission_response.html.find("div", class_="error")
        self.assertEqual(
            "Could not find a submission corresponding to this code that requires co-signing",
            error_node.text.strip(),
        )

    def test_submission_already_cosigned_raises_error(self):
        submission = SubmissionFactory.from_components(
            form__authentication_backend="digid",
            form__authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
            completed=True,
            public_registration_reference="OF-123456",
            cosign_complete=True,  # Already co-signed
            form__slug="form-to-cosign",
            form_url="http://url-to-form.nl/startpagina",
        )
        session = self.app.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
            "loa": DIGID_DEFAULT_LOA,
        }
        session.save()

        response = self.app.get(
            reverse(
                "submissions:find-submission-for-cosign",
                kwargs={"form_slug": "form-to-cosign"},
            )
        )

        form = response.forms[0]
        form["code"] = submission.public_registration_reference
        submission_response = form.submit()

        self.assertEqual(200, submission_response.status_code)

        error_node = submission_response.html.find("div", class_="error")
        expected_message = _(
            "Could not find a submission corresponding to this code that requires co-signing"
        )
        self.assertEqual(error_node.text.strip(), expected_message)

    @override_settings(LANGUAGE_CODE="en")
    def test_logout_button(self):
        SubmissionFactory.from_components(
            form__authentication_backend="digid",
            form__authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
            completed=True,
            cosign_complete=False,
            form__slug="form-to-cosign",
            form_url="http://url-to-form.nl/startpagina",
            public_registration_reference="OF-IMAREFERENCE",
        )
        session = self.app.session
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
            "loa": DIGID_DEFAULT_LOA,
        }
        session.save()

        response = self.app.get(
            reverse(
                "submissions:find-submission-for-cosign",
                kwargs={"form_slug": "form-to-cosign"},
            )
        )

        form = response.forms[1]
        logout_response = form.submit().follow()

        title_node = logout_response.html.find("h1")

        self.assertEqual(title_node.text.strip(), "You successfully logged out.")


@tag("security-40", "GHSA-2g49-rfm6-5qj5")
class AccessControlTests(FrontendRedirectMixin, WebTest):
    def setUp(self) -> None:
        super().setUp()

        # Needed so that when we get self.app.session we get a session object and not a dict
        self.app.get("/", status=403)

    def test_submission_must_require_cosign(self):
        submission = SubmissionFactory.from_components(
            form__authentication_backend="digid",
            form__authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
            components_list=[
                {
                    "key": "textfield",
                    "type": "textfield",
                    "label": "Not cosign component",
                },
            ],
            submitted_data={"textfield": "misc"},
            completed=True,
            cosign_complete=False,
            form__slug="form-without-cosign",
            form_url="http://url-to-form.nl/startpagina",
            public_registration_reference="OF-IMAREFERENCE",
        )
        session = self.app.session
        assert isinstance(session, SessionBase)
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
            "loa": DIGID_DEFAULT_LOA,
        }
        session.save()

        response = self.app.get(
            reverse(
                "submissions:find-submission-for-cosign",
                kwargs={"form_slug": "form-without-cosign"},
            )
        )

        form = response.forms[0]
        form["code"] = submission.public_registration_reference
        submission_response = form.submit()

        self.assertEqual(submission_response.status_code, 200)

    def test_rate_limiting_on_submission_lookup_via_code(self):
        self.addCleanup(cache.clear)

        SubmissionFactory.from_components(
            form__authentication_backend="digid",
            form__authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
            completed=True,
            cosign_complete=False,
            form__slug="form-to-cosign",
            form_url="http://url-to-form.nl/startpagina",
            public_registration_reference="OF-IMAREFERENCE",
        )
        session = self.client.session
        assert isinstance(session, SessionBase)
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
            "loa": DIGID_DEFAULT_LOA,
        }
        session.save()
        url = reverse(
            "submissions:find-submission-for-cosign",
            kwargs={"form_slug": "form-to-cosign"},
        )
        num_lookups = 0

        def _try_lookup():
            nonlocal num_lookups
            num_lookups += 1
            return self.client.post(url, data={"code": f"OF-{num_lookups:0>6}"})

        # do 30 requests in a short time - this exceeds the configured rate limit
        last_response = _try_lookup()
        for __ in range(30):
            last_response = _try_lookup()

        self.assertEqual(last_response.status_code, 429)
