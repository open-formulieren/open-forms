from django.contrib.sessions.backends.base import SessionBase
from django.core import mail
from django.core.cache import cache
from django.test import override_settings, tag
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from digid_eherkenning.choices import DigiDAssuranceLevels
from django_webtest import WebTest

from openforms.authentication.constants import FORM_AUTH_SESSION_KEY
from openforms.authentication.contrib.digid.constants import DIGID_DEFAULT_LOA
from openforms.forms.tests.factories import FormFactory
from openforms.frontend.tests import FrontendRedirectMixin
from openforms.logging.models import TimelineLogProxy

from ..constants import COSIGN_VERIFICATION_SESSION_KEY
from ..models import CosignOTP
from .factories import SubmissionFactory


class SearchSubmissionForCosignViewTests(WebTest):
    def setUp(self) -> None:
        super().setUp()

        self.addCleanup(cache.clear)

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

        self.assertRedirects(
            submission_response,
            reverse(
                "submissions:otp-for-cosign", kwargs={"form_slug": "form-to-cosign"}
            ),
        )
        self.assertEqual(
            self.app.session[COSIGN_VERIFICATION_SESSION_KEY], submission.pk
        )
        # expect OTP email
        self.assertEqual(len(mail.outbox), 1)

        # expect an audit log entry
        logs = TimelineLogProxy.objects.for_object(submission).filter_event(
            "cosign_lookup_success"
        )
        self.assertEqual(logs.count(), 1)
        log = logs[0]
        self.assertEqual(log.extra_data["auth"]["value"], "*******82")
        self.assertEqual(log.extra_data["auth"]["attribute"], "bsn")
        self.assertEqual(log.extra_data["auth"]["plugin"], "digid")

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

        self.assertRedirects(
            response,
            reverse(
                "submissions:otp-for-cosign", kwargs={"form_slug": "form-to-cosign"}
            ),
        )
        self.assertEqual(
            self.app.session[COSIGN_VERIFICATION_SESSION_KEY], submission.pk
        )
        # expect OTP email
        self.assertEqual(len(mail.outbox), 1)

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

        self.assertNotIn(COSIGN_VERIFICATION_SESSION_KEY, self.app.session)
        self.assertEqual(len(mail.outbox), 0)

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

        self.assertNotIn(COSIGN_VERIFICATION_SESSION_KEY, self.app.session)
        self.assertEqual(len(mail.outbox), 0)

    def test_user_has_authenticated_with_wrong_plugin_and_submission_reference(self):
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
        assert isinstance(session, SessionBase)
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
            {"code": submission.public_registration_reference},
            status=403,
        )

        self.assertNotIn(COSIGN_VERIFICATION_SESSION_KEY, self.app.session)
        self.assertEqual(len(mail.outbox), 0)
        # expect an audit log entry
        logs = TimelineLogProxy.objects.for_object(submission).filter_event(
            "cosign_lookup_blocked"
        )
        self.assertEqual(logs.count(), 1)
        log = logs[0]
        self.assertEqual(log.extra_data["auth"]["value"], "123456782")
        self.assertEqual(log.extra_data["auth"]["attribute"], "bsn")
        self.assertEqual(log.extra_data["auth"]["plugin"], "not-digid")

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
        self.assertNotIn(COSIGN_VERIFICATION_SESSION_KEY, self.app.session)
        self.assertEqual(len(mail.outbox), 0)
        # expect an audit log entry
        logs = TimelineLogProxy.objects.for_object(submission.form).filter_event(
            "cosign_lookup_failed"
        )
        self.assertEqual(logs.count(), 1)
        log = logs[0]
        self.assertEqual(log.extra_data["auth"]["value"], "123456782")
        self.assertEqual(log.extra_data["auth"]["attribute"], "bsn")
        self.assertEqual(log.extra_data["auth"]["plugin"], "digid")
        self.assertEqual(log.extra_data["code"], "WRONG-REFERENCE")

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
        self.assertNotIn(COSIGN_VERIFICATION_SESSION_KEY, self.app.session)
        self.assertEqual(len(mail.outbox), 0)
        # expect an audit log entry
        logs = TimelineLogProxy.objects.for_object(submission).filter_event(
            "cosign_lookup_blocked"
        )
        self.assertEqual(logs.count(), 1)
        log = logs[0]
        self.assertEqual(log.extra_data["auth"]["value"], "123456782")
        self.assertEqual(log.extra_data["auth"]["attribute"], "bsn")
        self.assertEqual(log.extra_data["auth"]["plugin"], "digid")

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
        self.assertFormError(
            submission_response.context["form"],
            field=None,
            errors=_(
                "Could not find a submission corresponding to this code that "
                "requires co-signing"
            ),
        )
        self.assertNotIn(COSIGN_VERIFICATION_SESSION_KEY, self.app.session)
        self.assertEqual(len(mail.outbox), 0)
        # expect an audit log entry
        logs = TimelineLogProxy.objects.for_object(submission).filter_event(
            "cosign_lookup_blocked"
        )
        self.assertEqual(logs.count(), 1)
        log = logs[0]
        self.assertEqual(log.extra_data["auth"]["value"], "123456782")
        self.assertEqual(log.extra_data["auth"]["attribute"], "bsn")
        self.assertEqual(log.extra_data["auth"]["plugin"], "digid")

    @tag("security-40", "GHSA-2g49-rfm6-5qj5")
    def test_rate_limiting_on_submission_lookup_via_code(self):
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
        # expect an audit log entry
        log = (
            TimelineLogProxy.objects.for_object(submission.form)
            .filter_event("cosign_lookup_rate_limited")
            .last()
        )
        assert log is not None
        self.assertEqual(log.extra_data["auth"]["value"], "123456782")
        self.assertEqual(log.extra_data["auth"]["attribute"], "bsn")
        self.assertEqual(log.extra_data["auth"]["plugin"], "digid")

    @tag("security-40", "GHSA-2g49-rfm6-5qj5")
    def test_session_resets_on_navigating_back(self):
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
        response = self.app.get(
            url, {"code": submission.public_registration_reference}
        ).follow()
        assert COSIGN_VERIFICATION_SESSION_KEY in self.app.session
        self.assertTemplateUsed(response, "submissions/cosign_otp.html")

        # simulate navigating back
        response2 = response.click(description=_("Go back"))

        self.assertEqual(response2.status_code, 200)
        self.assertNotIn(COSIGN_VERIFICATION_SESSION_KEY, self.app.session)


class CosignOTPViewTests(FrontendRedirectMixin, WebTest):
    def setUp(self) -> None:
        super().setUp()

        self.addCleanup(cache.clear)

        # Needed so that when we get self.app.session we get a session object and not a dict
        self.app.get("/", status=403)

    def test_cannot_access_view_without_being_authenticated(self):
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
            form__authentication_backend="digid",
            form__authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
            form_url="http://url-to-form.nl/startpagina",
        )

        self.app.get(
            reverse(
                "submissions:otp-for-cosign", kwargs={"form_slug": "form-to-cosign"}
            ),
            status=403,
        )

    def test_cannot_access_view_with_incorrect_auth_plugin(self):
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
            form__authentication_backend="digid",
            form__authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
            form_url="http://url-to-form.nl/startpagina",
        )
        session = self.app.session
        assert isinstance(session, SessionBase)
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "not-digid",
            "attribute": "bsn",
            "value": "123456782",
        }
        session.save()

        self.app.get(
            reverse(
                "submissions:otp-for-cosign", kwargs={"form_slug": "form-to-cosign"}
            ),
            status=403,
        )

    def test_cannot_access_view_with_insufficient_loa_auth_plugin(self):
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
            form__authentication_backend="digid",
            form__authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
            form_url="http://url-to-form.nl/startpagina",
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

        self.app.get(
            reverse(
                "submissions:otp-for-cosign", kwargs={"form_slug": "form-to-cosign"}
            ),
            status=403,
        )

    def test_wrong_form_slug_results_in_404(self):
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
            form__authentication_backend="digid",
            form__authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
            form_url="http://url-to-form.nl/startpagina",
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

        self.app.get(
            reverse("submissions:otp-for-cosign", kwargs={"form_slug": "wrong-slug"}),
            status=404,
        )

    def test_requires_submission_reference_in_session(self):
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
            form__authentication_backend="digid",
            form__authentication_backend_options={"loa": DigiDAssuranceLevels.high},
            form_url="http://url-to-form.nl/startpagina",
        )
        session = self.app.session
        assert isinstance(session, SessionBase)
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
            "loa": DigiDAssuranceLevels.base,
        }
        assert COSIGN_VERIFICATION_SESSION_KEY not in session
        session.save()

        self.app.get(
            reverse(
                "submissions:otp-for-cosign", kwargs={"form_slug": "form-to-cosign"}
            ),
            status=403,
        )

    def test_requires_submission_form_matches_form_slug_url_kwarg(self):
        submission = SubmissionFactory.from_components(
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
            form__authentication_backend="digid",
            form__authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
            form_url="http://url-to-form.nl/startpagina",
        )
        FormFactory.create(
            slug="other-form",
            authentication_backend="digid",
            authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
        )
        session = self.app.session
        assert isinstance(session, SessionBase)
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
            "loa": DIGID_DEFAULT_LOA,
        }
        session[COSIGN_VERIFICATION_SESSION_KEY] = submission.pk
        session.save()

        self.app.get(
            reverse("submissions:otp-for-cosign", kwargs={"form_slug": "other-form"}),
            status=403,
        )

        # expect an audit log entry
        logs = TimelineLogProxy.objects.for_object(submission).filter_event(
            "cosign_otp_blocked"
        )
        self.assertEqual(logs.count(), 1)
        log = logs[0]
        self.assertEqual(log.extra_data["auth"]["value"], "123456782")
        self.assertEqual(log.extra_data["auth"]["attribute"], "bsn")
        self.assertEqual(log.extra_data["auth"]["plugin"], "digid")

    def test_requires_submission_waiting_for_cosign(self):
        submission = SubmissionFactory.from_components(
            components_list=[
                {
                    "key": "cosign",
                    "type": "cosign",
                    "label": "Cosign component",
                    "validate": {"required": True},
                },
            ],
            submitted_data={"cosign": "test@test.nl"},
            form__slug="form-to-cosign",
            form__authentication_backend="digid",
            form__authentication_backend_options={"loa": DIGID_DEFAULT_LOA},
            form_url="http://url-to-form.nl/startpagina",
            cosigned=True,
            co_sign_data__plugin="digid",
        )
        assert not submission.cosign_state.is_waiting
        session = self.app.session
        assert isinstance(session, SessionBase)
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
            "loa": DIGID_DEFAULT_LOA,
        }
        session[COSIGN_VERIFICATION_SESSION_KEY] = submission.pk
        session.save()

        self.app.get(
            reverse(
                "submissions:otp-for-cosign", kwargs={"form_slug": "form-to-cosign"}
            ),
            status=403,
        )

        # expect an audit log entry
        logs = TimelineLogProxy.objects.for_object(submission).filter_event(
            "cosign_otp_blocked"
        )
        self.assertEqual(logs.count(), 1)
        log = logs[0]
        self.assertEqual(log.extra_data["auth"]["value"], "123456782")
        self.assertEqual(log.extra_data["auth"]["attribute"], "bsn")
        self.assertEqual(log.extra_data["auth"]["plugin"], "digid")

    @tag("security-40", "GHSA-2g49-rfm6-5qj5")
    def test_rate_limiting_on_cosign_otp(self):
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
        session = self.client.session
        assert isinstance(session, SessionBase)
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
            "loa": DIGID_DEFAULT_LOA,
        }
        session[COSIGN_VERIFICATION_SESSION_KEY] = submission.pk
        session.save()
        url = reverse(
            "submissions:otp-for-cosign", kwargs={"form_slug": "form-to-cosign"}
        )

        num_attempts = 0

        def _attempt_otp_bruteforce():
            nonlocal num_attempts
            num_attempts += 1
            return self.client.post(url, data={"otp": f" 000-{num_attempts:0>3} "})

        # do 30 requests in a short time - this exceeds the configured rate limit
        last_response = _attempt_otp_bruteforce()
        for __ in range(30):
            last_response = _attempt_otp_bruteforce()

        self.assertEqual(last_response.status_code, 429)
        # expect an audit log entry
        log = (
            TimelineLogProxy.objects.for_object(submission)
            .filter_event("cosign_otp_rate_limited")
            .last()
        )
        assert log is not None
        self.assertEqual(log.extra_data["auth"]["value"], "123456782")
        self.assertEqual(log.extra_data["auth"]["attribute"], "bsn")
        self.assertEqual(log.extra_data["auth"]["plugin"], "digid")

    def test_requires_valid_otp(self):
        """
        Assert that the entire flow leads to a redirect to the frontend.
        """
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
        assert isinstance(session, SessionBase)
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
            "loa": DIGID_DEFAULT_LOA,
        }
        session.save()

        # start with lookup by code -> navigate to OTP page
        otp_response = self.app.get(
            reverse(
                "submissions:find-submission-for-cosign",
                kwargs={"form_slug": "form-to-cosign"},
            ),
            {"code": submission.public_registration_reference},
        ).follow()
        # ensure no OTP exists at all
        CosignOTP.objects.all().delete()

        form = otp_response.forms[0]
        form["otp"] = "007-420"  # invalid code, but right format
        submission_response = form.submit()

        self.assertEqual(submission_response.status_code, 200)
        self.assertIn(COSIGN_VERIFICATION_SESSION_KEY, self.app.session)

        # expect an audit log entry
        logs = TimelineLogProxy.objects.for_object(submission).filter_event(
            "cosign_otp_blocked"
        )
        self.assertEqual(logs.count(), 1)
        log = logs[0]
        self.assertEqual(log.extra_data["auth"]["value"], "123456782")
        self.assertEqual(log.extra_data["auth"]["attribute"], "bsn")
        self.assertEqual(log.extra_data["auth"]["plugin"], "digid")

    def test_requires_non_expired_otp(self):
        """
        Assert that the entire flow leads to a redirect to the frontend.
        """
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
        assert isinstance(session, SessionBase)
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
            "loa": DIGID_DEFAULT_LOA,
        }
        session.save()

        # start with lookup by code -> navigate to OTP page
        otp_response = self.app.get(
            reverse(
                "submissions:find-submission-for-cosign",
                kwargs={"form_slug": "form-to-cosign"},
            ),
            {"code": submission.public_registration_reference},
        ).follow()
        # mark the OTP as expired
        cosign_otp = CosignOTP.objects.get()
        cosign_otp.expires_at = timezone.now()
        cosign_otp.save()
        assert cosign_otp.is_expired

        form = otp_response.forms[0]
        form["otp"] = cosign_otp.verification_code
        submission_response = form.submit()

        self.assertEqual(submission_response.status_code, 200)
        self.assertIn(COSIGN_VERIFICATION_SESSION_KEY, self.app.session)

        # expect an audit log entry
        logs = TimelineLogProxy.objects.for_object(submission).filter_event(
            "cosign_otp_blocked"
        )
        self.assertEqual(logs.count(), 1)
        log = logs[0]
        self.assertEqual(log.extra_data["auth"]["value"], "123456782")
        self.assertEqual(log.extra_data["auth"]["attribute"], "bsn")
        self.assertEqual(log.extra_data["auth"]["plugin"], "digid")

    def test_successfully_start_cosign_process(self):
        """
        Assert that the entire flow leads to a redirect to the frontend.
        """
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
        assert isinstance(session, SessionBase)
        session[FORM_AUTH_SESSION_KEY] = {
            "plugin": "digid",
            "attribute": "bsn",
            "value": "123456782",
            "loa": DIGID_DEFAULT_LOA,
        }
        session.save()

        # start with lookup by code -> navigate to OTP page
        otp_response = self.app.get(
            reverse(
                "submissions:find-submission-for-cosign",
                kwargs={"form_slug": "form-to-cosign"},
            ),
            {"code": submission.public_registration_reference},
        ).follow()
        # a OTP record must be created, look it up to grab the code
        otp_code = CosignOTP.objects.get().verification_code

        form = otp_response.forms[0]
        form["otp"] = otp_code
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
        self.assertNotIn(COSIGN_VERIFICATION_SESSION_KEY, self.app.session)
        # expect an audit log entry
        logs = TimelineLogProxy.objects.for_object(submission).filter_event(
            "cosign_otp_success"
        )
        self.assertEqual(logs.count(), 1)
        log = logs[0]
        self.assertEqual(log.extra_data["auth"]["value"], "*******82")
        self.assertEqual(log.extra_data["auth"]["attribute"], "bsn")
        self.assertEqual(log.extra_data["auth"]["plugin"], "digid")
