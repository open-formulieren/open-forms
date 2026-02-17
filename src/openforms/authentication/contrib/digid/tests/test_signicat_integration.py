from typing import Literal
from unittest.mock import patch

from django.core.files import File
from django.template.response import TemplateResponse
from django.test import TestCase, override_settings
from django.urls import reverse

import requests
from digid_eherkenning.choices import ConfigTypes, DigiDAssuranceLevels, XMLContentTypes
from digid_eherkenning.models import ConfigCertificate, DigidConfiguration
from freezegun import freeze_time
from furl import furl
from privates.test import temp_private_root
from simple_certmanager.test.factories import CertificateFactory

from openforms.forms.tests.factories import FormStepFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tokens import submission_resume_token_generator
from openforms.utils.tests.cache import clear_caches
from openforms.utils.tests.html_forms import parse_form
from openforms.utils.tests.vcr import OFVCRMixin

from ....constants import FORM_AUTH_SESSION_KEY
from ..constants import PLUGIN_ID
from .utils import TEST_FILES

KEY = TEST_FILES / "our_key.pem"
CERT = TEST_FILES / "our_certificate.pem"
METADATA = TEST_FILES / "signicat_metadata.xml"

SIGNICAT_BROKER_BASE = furl("https://maykin.pre.ie01.signicat.pro/broker")


@patch(
    "openforms.submissions.tokens.submission_resume_token_generator.secret", new="dummy"
)
@patch(
    "onelogin.saml2.authn_request.OneLogin_Saml2_Utils.generate_unique_id",
    lambda *_, **__: "ONELOGIN_123456",
)
@temp_private_root()
@override_settings(COOKIE_CONSENT_ENABLED=False)
class SignicatDigiDIntegrationTests(OFVCRMixin, TestCase):
    """Test using Signicat broker.

    Instead of mocking responses. We do real requests to a Signicat test environment
    *once* and record the responses with VCR.

    Requests to ourself go through the regular Django TestClient.
    Requests to the broker use a requests Session.

    When Signicat updates their service, responses on VCR cassettes might be stale, and
    we'll need to re-test against the real service to assert everything still works.

    To do so:

    #. Ensure the config is still valid:
       - `CERT` needs to be valid
       - `CERT` and our SAML metadata need to be configured in Signicat
       - `METADATA` needs to contain their SAML metadata
    #. Delete the VCR cassettes
    #. Run the test
    #. Inspect the diff of the new cassettes

    The default dev settings set the record mode to 'once', but if you need a difference
    once, see the :module:`openforms.utils.tests.vcr` documentation.
    """

    VCR_TEST_FILES = TEST_FILES

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cert = CertificateFactory.create(
            label="DigiD",
            with_private_key=True,
            public_certificate__from_path=CERT,
            private_key__from_path=KEY,
        )

        config = DigidConfiguration.get_solo()
        # broker insists using https
        config.base_url = config.entity_id = "https://localhost:8000"
        # config.authn_requests_signed =  False
        config.idp_service_entity_id = SIGNICAT_BROKER_BASE / "sp/saml"
        config.artifact_resolve_content_type = XMLContentTypes.text_xml
        config.attribute_consuming_service_index = "1"
        config.service_name = "Test"
        config.requested_attributes = [{"name": "bsn", "required": True}]
        config.want_assertions_signed = False
        config.want_assertions_encrypted = False
        config.slo = False

        with METADATA.open("rb") as md_file:
            config.idp_metadata_file = File(md_file, METADATA.name)
            config.save()

        config_cert = ConfigCertificate.objects.create(
            config_type=ConfigTypes.digid, certificate=cert
        )
        # Will fail if/when the certificate expires
        assert config_cert.is_ready_for_authn_requests

    def setUp(self):
        super().setUp()

        clear_caches()
        self.addCleanup(clear_caches)

        # We're freezing the time to whatever is on the cassette, because parts of the
        # body of the SAML messages are time dependant. (e.g. expiration datetimes)
        #
        # (this is funny if you're old enough to have seen your VCR with a blinking time
        # and it missed recording episodes during your holiday)
        if self.cassette.responses:
            now = self.cassette.responses[0]["headers"]["date"][0]
            time_ctx = freeze_time(now)
            self.addCleanup(time_ctx.stop)
            time_ctx.start()

    def test_login_with_too_low_a_loa_fails(self):
        session: requests.Session = requests.Session()
        form = FormStepFactory.create(
            form__slug="slurm",
            form__authentication_backend=PLUGIN_ID,
            form__authentication_backend_options={
                "loa": DigiDAssuranceLevels.substantial
            },
            form_definition__login_required=True,
        ).form

        login_url = reverse(
            "authentication:start", kwargs={"slug": form.slug, "plugin_id": PLUGIN_ID}
        )
        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = furl("http://testserver/") / form_path

        our_faux_redirect = self.client.get(
            login_url, {"next": str(form_url)}, follow=True
        )
        sim_method, sim_action_url, sim_form = _do_signicat_login(
            session, our_faux_redirect
        )

        # select LoA lower than substantial/loa3
        sim_form["loa"] = "loa2plus"
        auth_response = session.request(sim_method, sim_action_url, data=sim_form)
        self.assertFalse(auth_response.ok)

    def test_login_with_a_high_loa_succeeds(self):
        session: requests.Session = requests.session()
        form = FormStepFactory.create(
            form__slug="slurm",
            form__authentication_backend=PLUGIN_ID,
            form__authentication_backend_options={
                "loa": DigiDAssuranceLevels.substantial
            },
            form_definition__login_required=True,
        ).form

        login_url = reverse(
            "authentication:start", kwargs={"slug": form.slug, "plugin_id": PLUGIN_ID}
        )
        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = furl("https://testserver") / form_path

        our_faux_redirect = self.client.get(
            login_url, {"next": str(form_url)}, follow=True
        )
        sim_method, sim_action_url, sim_form = _do_signicat_login(
            session, our_faux_redirect
        )

        # select LOA higher than substantial/loa3
        sim_form["loa"] = "loa4"
        auth_response = session.request(
            sim_method, sim_action_url, data=sim_form, allow_redirects=False
        )

        # redirect back to our acs
        self.assertEqual(auth_response.status_code, 302)
        acs_url = furl(auth_response.headers["location"])

        self.assertEqual(acs_url.scheme, "https")
        self.assertEqual(acs_url.netloc, "localhost:8000")

        # prep the URL for Django test client consumption
        acs_url.remove(netloc=True, scheme=True)
        acs_response = self.client.get(acs_url.url, follow=True)

        # we are logged in
        self.assertIn(FORM_AUTH_SESSION_KEY, self.client.session)
        # and we end up starting the form
        self.assertEqual(acs_response.resolver_match.view_name, "core:form-detail")
        self.assertEqual(acs_response.resolver_match.kwargs["slug"], "slurm")

    def test_resuming_a_suspended_submission(self):
        session: requests.Session = requests.session()
        form = FormStepFactory.create(
            form__slug="slurm",
            form__authentication_backend=PLUGIN_ID,
            form__authentication_backend_options={
                "loa": DigiDAssuranceLevels.substantial
            },
            form_definition__login_required=True,
        ).form
        submission = SubmissionFactory.create(
            uuid="17399e4c-913f-47de-837a-d71a8308e0a8",  # part for the RelayState
            form=form,
            form_url=furl("https://testserver").join(form.get_absolute_url()),
            auth_info__plugin=PLUGIN_ID,
            auth_info__value="900026236",
            auth_info__loa=DigiDAssuranceLevels.substantial,
        )
        resume_path = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        our_faux_redirect = self.client.get(resume_path, follow=True)
        sim_method, sim_action_url, sim_form = _do_signicat_login(
            session, our_faux_redirect
        )

        # select LOA higher than substantial/loa3
        sim_form["loa"] = "loa4"
        auth_response = session.request(
            sim_method, sim_action_url, data=sim_form, allow_redirects=False
        )

        # redirect back to our acs
        self.assertEqual(auth_response.status_code, 302)
        acs_url = furl(auth_response.headers["location"])

        self.assertEqual(acs_url.scheme, "https")
        self.assertEqual(acs_url.netloc, "localhost:8000")

        # prep the url for django testclient consumption
        acs_url.remove(netloc=True, scheme=True)
        acs_response = self.client.get(acs_url.url, follow=True)

        # we end up starting the form
        self.assertEqual(acs_response.resolver_match.view_name, "core:form-detail")
        self.assertEqual(acs_response.resolver_match.kwargs["slug"], "slurm")

    def test_cannot_resume_someone_elses_submission(self):
        session: requests.Session = requests.session()
        form = FormStepFactory.create(
            form__slug="slurm",
            form__authentication_backend=PLUGIN_ID,
            form__authentication_backend_options={
                "loa": DigiDAssuranceLevels.substantial
            },
            form_definition__login_required=True,
        ).form
        submission = SubmissionFactory.create(
            uuid="17399e4c-913f-47de-837a-d71a8308e0a8",  # part for the RelayState
            form=form,
            form_url=furl("https://testserver").join(form.get_absolute_url()),
            auth_info__plugin=PLUGIN_ID,
            auth_info__value="900026236",
            auth_info__loa=DigiDAssuranceLevels.substantial,
        )
        resume_path = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        our_faux_redirect = self.client.get(resume_path, follow=True)
        sim_method, sim_action_url, sim_form = _do_signicat_login(
            session, our_faux_redirect
        )

        # select LOA higher than substantial/loa3
        sim_form["loa"] = "loa4"
        # but we are a different person
        sim_form["bsn"] = "330660688"
        auth_response = session.request(
            sim_method, sim_action_url, data=sim_form, allow_redirects=False
        )

        # redirect back to our acs
        self.assertEqual(auth_response.status_code, 302)
        acs_url = furl(auth_response.headers["location"])

        self.assertEqual(acs_url.scheme, "https")
        self.assertEqual(acs_url.netloc, "localhost:8000")

        # prep the url for django testclient consumption
        acs_url.remove(netloc=True, scheme=True)
        acs_response = self.client.get(acs_url.url, follow=True)

        # we are not allowed to resume
        self.assertEqual(acs_response.status_code, 403)

    def test_resuming_checks_loa_too(self):
        session: requests.Session = requests.session()
        form = FormStepFactory.create(
            form__slug="slurm",
            form__authentication_backend=PLUGIN_ID,
            form__authentication_backend_options={
                "loa": DigiDAssuranceLevels.substantial
            },
            form_definition__login_required=True,
        ).form
        submission = SubmissionFactory.create(
            uuid="17399e4c-913f-47de-837a-d71a8308e0a8",  # part for the RelayState
            form=form,
            form_url=furl("https://testserver").join(form.get_absolute_url()),
            auth_info__plugin=PLUGIN_ID,
            auth_info__value="900026236",
            auth_info__loa=DigiDAssuranceLevels.substantial,
        )
        resume_path = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        our_faux_redirect = self.client.get(resume_path, follow=True)
        sim_method, sim_action_url, sim_form = _do_signicat_login(
            session, our_faux_redirect
        )

        # select LOA lower than substantial/loa3
        sim_form["loa"] = "loa2"
        auth_response = session.request(
            sim_method, sim_action_url, data=sim_form, allow_redirects=False
        )

        # Signicat catches the LOA requirement is not met
        self.assertFalse(auth_response.ok)

    def test_resuming_checks_with_current_loa_of_form(self):
        session: requests.Session = requests.session()
        form = FormStepFactory.create(
            form__slug="slurm",
            form__authentication_backend=PLUGIN_ID,
            form__authentication_backend_options={"loa": DigiDAssuranceLevels.high},
            form_definition__login_required=True,
        ).form
        submission = SubmissionFactory.create(
            uuid="17399e4c-913f-47de-837a-d71a8308e0a8",  # part for the RelayState
            form=form,
            form_url=furl("https://testserver").join(form.get_absolute_url()),
            auth_info__plugin=PLUGIN_ID,
            auth_info__value="900026236",
            auth_info__loa=DigiDAssuranceLevels.substantial,  # this used to be fine
        )
        resume_path = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        our_faux_redirect = self.client.get(resume_path, follow=True)
        sim_method, sim_action_url, sim_form = _do_signicat_login(
            session, our_faux_redirect
        )

        # select LOA lower to substantial/loa3
        sim_form["loa"] = "loa3"
        auth_response = session.request(
            sim_method, sim_action_url, data=sim_form, allow_redirects=False
        )

        # But since saving for resuming, the form LOA was changed to high so
        # Signicat catches the LOA requirement is not met
        self.assertFalse(auth_response.ok)

    def test_raising_loa_requirements_fails_in_flight_authentications(self):
        form_step = FormStepFactory.create(
            form__slug="slurm",
            form__authentication_backend=PLUGIN_ID,
            form__authentication_backend_options={"loa": DigiDAssuranceLevels.middle},
            form_definition__login_required=True,
        )
        form = form_step.form
        auth_backend = form.auth_backends.get()
        submission = SubmissionFactory.create(
            uuid="17399e4c-913f-47de-837a-d71a8308e0a8",  # part for the RelayState
            form=form,
            form_url=furl("https://testserver").join(form.get_absolute_url()),
            auth_info__plugin=PLUGIN_ID,
            auth_info__value="900026236",
            auth_info__loa=DigiDAssuranceLevels.middle,
        )
        resume_path = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        with requests.Session() as session:
            our_faux_redirect = self.client.get(resume_path, follow=True)
            sim_method, sim_action_url, sim_form = _do_signicat_login(
                session, our_faux_redirect
            )
            # copy for later
            sim_method_2, sim_action_url_2, sim_form_2 = (
                sim_method,
                sim_action_url,
                sim_form,
            )

            # select substantial LOA
            sim_form["loa"] = "loa3"
            auth_response = session.request(
                sim_method, sim_action_url, data=sim_form, allow_redirects=False
            )

            # redirect back to our acs
            self.assertEqual(auth_response.status_code, 302)
            acs_url = furl(auth_response.headers["location"])

            self.assertEqual(acs_url.scheme, "https")
            self.assertEqual(acs_url.netloc, "localhost:8000")

            # prep the url for django testclient consumption
            acs_url.remove(netloc=True, scheme=True)

            # but in the meanwhile the form designer goes all-in
            auth_backend.options["loa"] = DigiDAssuranceLevels.high
            form.save()
            clear_caches()

            acs_response = self.client.get(acs_url.url, follow=True)
            assert acs_response.status_code == 200
            # we are not not logged in
            self.assertNotIn(FORM_AUTH_SESSION_KEY, self.client.session)

        # create a separate session, since Signicat seems to remember the original login,
        # resulting in being redirected immediately to https://localhost:8000 which doesn't
        # resolve of course
        with requests.Session() as session2:
            # and are redirected back to the broker
            # do the JS submit to get redirected to signicat broker
            method_2, redirect_url_2, form_values_2 = _parse_form(acs_response)
            self.assertTrue(
                session2.request(method_2, redirect_url_2, data=form_values_2).ok
            )

            sim_response_2 = session2.get(
                str(SIGNICAT_BROKER_BASE / "authn/simulator/authenticate/digid")
            )
            self.assertTrue(sim_response_2.ok)

            # select substantial LOA
            sim_form_2["loa"] = "loa4"
            auth_response_2 = session2.request(
                sim_method_2, sim_action_url_2, data=sim_form_2, allow_redirects=False
            )

        # redirect back to our acs
        self.assertEqual(auth_response_2.status_code, 302)
        acs_url_2 = furl(auth_response_2.headers["location"])
        # prep the url for django testclient consumption
        acs_url_2.remove(netloc=True, scheme=True)
        acs_response_2 = self.client.get(acs_url_2.url, follow=True)

        # we are logged in
        self.assertTrue(submission.is_authenticated)
        # and we end up starting the form
        self.assertEqual(acs_response_2.resolver_match.view_name, "core:form-detail")
        self.assertEqual(acs_response_2.resolver_match.kwargs["slug"], "slurm")

    def test_test_key_material_is_not_fishing_bait(self):
        config = DigidConfiguration.get_solo()
        config.base_url = "https://sharkbait.example.com"
        config.save()
        self.addCleanup(DigidConfiguration.clear_cache)

        session: requests.Session = requests.session()
        form = FormStepFactory.create(
            form__slug="slurm",
            form__authentication_backend=PLUGIN_ID,
            form__authentication_backend_options={"loa": DigiDAssuranceLevels.base},
            form_definition__login_required=True,
        ).form

        login_url = reverse(
            "authentication:start", kwargs={"slug": form.slug, "plugin_id": PLUGIN_ID}
        )
        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = furl("http://testserver/") / form_path

        our_faux_redirect = self.client.get(
            login_url, {"next": str(form_url)}, follow=True
        )
        sim_method, sim_action_url, sim_form = _do_signicat_login(
            session,
            our_faux_redirect,
            with_idp_selection=True,
        )

        auth_response = session.request(
            sim_method, sim_action_url, data=sim_form, allow_redirects=False
        )

        # not redirected
        self.assertFalse(auth_response.ok)


# class SignicatWithEncryptedAssertionsTests(SignicatDigiDIntegrationTests):
#     """This doens't work; after changing our DigidConfiguration, we need to send our updated
#     SAML metadata to the broker (Signicat)
#
#     To test this we'd need to configure a separate entityID
#     (perhaps with a different certificate/key pair) and set it up with Signicat
#     """
#
#
#     @classmethod
#     def setUpTestData(cls):
#         super().setUpTestData()
#
#         config = DigidConfiguration.get_solo()
#         config.want_assertions_encrypted = True
#         config.save()

# class SignicatWithUnsignedAssertionsTests(SignicatDigiDIntegrationTests):
#     """These pass, but Signicat signs assertions, because it will follow
#     the metadata we uploaded previously, which wanted assertions signed.
#
#     Our SAML metadata discovery url is unreachable...
#     https://localhost:8000/discovery/digid-eherkenning/digid
#
#     I don't know if this is used in a live, non-testing environment.
#     """
#
#
#     @classmethod
#     def setUpTestData(cls):
#         super().setUpTestData()
#
#         config = DigidConfiguration.get_solo()
#         config.want_assertions_signed = False
#         config.save()

# Same same, but different
# class SignicatWithSingnedAndEncryptedAssertionsTests(SignicatDigiDIntegrationTests):
#     @classmethod
#     def setUpTestData(cls):
#         super().setUpTestData()
#
#         config = DigidConfiguration.get_solo()
#         config.want_assertions_signed = True
#         config.want_assertions_encrypted = True
#         config.save()


# Helper functions

# poor person's enum.StrEnum
type Method = Literal["get", "post"]
type Response = TemplateResponse | requests.Response


def _do_signicat_login(
    session: requests.Session,
    our_redirect: TemplateResponse,
    with_idp_selection: bool = False,
) -> tuple[Method, str, dict[str, str]]:
    """
    Receive the JS-auto-submit (template) response and simulate the auto-submit.

    This handles the signicat login screens until we redirect back to Open Forms.
    """
    # do the JS submit to get redirected to Signicat broker
    method, redirect_url, form_values = _parse_form(our_redirect)
    saml_submit_response = session.request(method, redirect_url, data=form_values)
    assert saml_submit_response.ok

    if with_idp_selection:
        # select 'simulator' from the IdP selector screen
        idp_response = session.get(
            str(SIGNICAT_BROKER_BASE / "select/authn"),
            params={"connectionId": "simulator"},
        )
        assert idp_response.ok

    # select EHerkenning from the Signicat simulator selection screen
    sim_response = session.get(
        str(SIGNICAT_BROKER_BASE / "authn/simulator/authenticate/digid")
    )
    assert sim_response.ok

    sim_method, sim_action_url, sim_form = _parse_form(sim_response)
    return sim_method, sim_action_url, sim_form


def _parse_form(response: Response) -> tuple[Method, str, dict[str, str]]:
    """
    Extract method, action URL and form values from html content.
    """
    method, action, submit_fields = parse_form(response.content)
    url: str = action or response.url
    assert url, "No url found"
    return method, url, submit_fields
