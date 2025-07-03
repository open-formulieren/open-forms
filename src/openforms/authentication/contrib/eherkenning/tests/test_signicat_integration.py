from typing import Literal
from unittest.mock import patch

from django.core.files import File
from django.template.response import TemplateResponse
from django.test import TestCase, override_settings
from django.urls import reverse

import requests
from digid_eherkenning.choices import AssuranceLevels, ConfigTypes, XMLContentTypes
from digid_eherkenning.models import ConfigCertificate, EherkenningConfiguration
from freezegun import freeze_time
from furl import furl
from privates.test import temp_private_root
from simple_certmanager.test.factories import CertificateFactory
from webtest.forms import Form as WTForm

from openforms.forms.tests.factories import FormStepFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tokens import submission_resume_token_generator
from openforms.utils.tests.cache import clear_caches
from openforms.utils.tests.vcr import OFVCRMixin

from ....constants import FORM_AUTH_SESSION_KEY
from .utils import TEST_FILES

PLUGIN_ID = "eherkenning"
KEY = TEST_FILES / "our_key.pem"
CERT = TEST_FILES / "our_certificate.pem"
METADATA = TEST_FILES / "signicat_metadata.xml"

SIGNICAT_BROKER_BASE = furl("https://maykin.pre.ie01.signicat.pro/broker")
SELECT_EHERKENNING_SIM = (
    SIGNICAT_BROKER_BASE / "authn/simulator/authenticate/eherkenning"
)


@patch(
    "openforms.submissions.tokens.submission_resume_token_generator.secret", new="dummy"
)
@patch(
    "onelogin.saml2.authn_request.OneLogin_Saml2_Utils.generate_unique_id",
    lambda *_, **__: "ONELOGIN_123456",
)
@temp_private_root()
@override_settings(COOKIE_CONSENT_ENABLED=False)
class SignicatEHerkenningIntegrationTests(OFVCRMixin, TestCase):
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
            label="EHerkenning",
            with_private_key=True,
            public_certificate__from_path=CERT,
            private_key__from_path=KEY,
        )

        config = EherkenningConfiguration.get_solo()
        config.idp_service_entity_id = SIGNICAT_BROKER_BASE / "sp/saml"
        # broker insists using https
        config.entity_id = "https://localhost:8000/eherkenning"
        config.base_url = "https://localhost:8000"
        config.artifact_resolve_content_type = XMLContentTypes.text_xml
        config.want_assertions_signed = True
        config.want_assertions_encrypted = False

        config.service_name = "eHerkenning test"
        config.service_description = "CI eHerkenning SAML integration test"
        config.oin = "00000001002220647000"
        config.makelaar_id = "00000003244440010000"
        config.privacy_policy = "https://example.com"
        config.service_language = "nl"

        config.eh_requested_attributes = [
            "urn:etoegang:1.9:EntityConcernedID:KvKnr",
            "urn:etoegang:1.9:EntityConcernedID:Pseudo",
        ]
        config.eh_attribute_consuming_service_index = "9052"
        config.eh_service_uuid = "588932b9-28ae-4323-ab6c-fabbddae05cd"
        config.eh_service_instance_uuid = "952cee6a-6553-4f58-922d-dd03486a772c"
        config.eh_loa = AssuranceLevels.low_plus

        config.no_eidas = True

        with METADATA.open("rb") as md_file:
            config.idp_metadata_file = File(md_file, METADATA.name)
            config.save()

        config_cert = ConfigCertificate.objects.create(
            config_type=ConfigTypes.eherkenning, certificate=cert
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

    def test_login_with_a_high_loa_succeeds(self):
        session: requests.Session = requests.session()
        form = FormStepFactory.create(
            form__slug="slurm",
            form__authentication_backend=PLUGIN_ID,
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
        # do the JS submit to get redirected to Signicat broker
        method, redirect_url, form_values = _parse_form(our_faux_redirect)
        self.assertTrue(session.request(method, redirect_url, data=form_values).ok)

        # select EHerkenning from the Signicat simulator selection screen
        sim_response = session.get(SELECT_EHERKENNING_SIM)
        self.assertTrue(sim_response.ok)

        sim_method, sim_action_url, sim_form = _parse_form(sim_response)
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
        assert acs_response.status_code == 200

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
            form_definition__login_required=True,
        ).form
        submission = SubmissionFactory.create(
            uuid="17399e4c-913f-47de-837a-d71a8308e0a8",  # part for the RelayState
            form=form,
            form_url=furl("https://testserver").join(form.get_absolute_url()),
            auth_info__plugin=PLUGIN_ID,
            auth_info__value="24444001",
            auth_info__attribute="kvk",
            auth_info__loa=AssuranceLevels.substantial,
        )
        resume_path = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        our_faux_redirect = self.client.get(resume_path, follow=True)

        self.assertEqual(our_faux_redirect.status_code, 200)
        # do the JS submit to get redirected to signicat broker
        method, redirect_url, form_values = _parse_form(our_faux_redirect)
        self.assertTrue(session.request(method, redirect_url, data=form_values).ok)

        # select eherkenning from the signicat simulator selection screen
        sim_response = session.get(SELECT_EHERKENNING_SIM)
        self.assertTrue(sim_response.ok)

        sim_method, sim_action_url, sim_form = _parse_form(sim_response)
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
            form_definition__login_required=True,
        ).form
        submission = SubmissionFactory.create(
            uuid="17399e4c-913f-47de-837a-d71a8308e0a8",  # part for the RelayState
            form=form,
            form_url=furl("https://testserver").join(form.get_absolute_url()),
            auth_info__plugin=PLUGIN_ID,
            auth_info__value="24444001",
            auth_info__attribute="kvk",
            auth_info__loa=AssuranceLevels.substantial,
        )
        resume_path = reverse(
            "submissions:resume",
            kwargs={
                "token": submission_resume_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )

        our_faux_redirect = self.client.get(resume_path, follow=True)

        self.assertEqual(our_faux_redirect.status_code, 200)
        # do the JS submit to get redirected to signicat broker
        method, redirect_url, form_values = _parse_form(our_faux_redirect)
        self.assertTrue(session.request(method, redirect_url, data=form_values).ok)

        # select eherkenning from the signicat simulator selection screen
        sim_response = session.get(SELECT_EHERKENNING_SIM)
        self.assertTrue(sim_response.ok)

        sim_method, sim_action_url, sim_form = _parse_form(sim_response)
        # select LOA higher than substantial/loa3
        sim_form["loa"] = "loa4"
        # but we are a different person
        sim_form["entityConcernedIdKvKnr"] = "12345678"
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

    def test_key_material_is_not_fishing_bait(self):
        config = EherkenningConfiguration.get_solo()
        config.base_url = "https://sharkbait.example.com"
        config.save()

        def reset_config():
            config.base_url = config.entity_id = "https://localhost:8000"
            config.save()

        self.addCleanup(reset_config)

        session: requests.Session = requests.session()
        form = FormStepFactory.create(
            form__slug="slurm",
            form__authentication_backend=PLUGIN_ID,
            form_definition__login_required=True,
        ).form

        login_url = reverse(
            "authentication:start", kwargs={"slug": form.slug, "plugin_id": PLUGIN_ID}
        )
        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = furl("http://testserver/") / form_path

        our_faux_redirect = self.client.get(f"{login_url}?next={form_url}", follow=True)
        # do the JS submit to get redirected to signicat broker
        method, redirect_url, form_values = _parse_form(our_faux_redirect)
        session.request(method, redirect_url, data=form_values)
        sim_response = session.get(SELECT_EHERKENNING_SIM)
        sim_method, sim_action_url, sim_form = _parse_form(sim_response)
        auth_response = session.request(
            sim_method, sim_action_url, data=sim_form, allow_redirects=False
        )
        # not redirected
        self.assertFalse(auth_response.ok)


# class SignicatWithEncryptedAssertionsTests(SignicatEHerkenningIntegrationTests):
#     """This doens't work; after changing our EherkenningConfiguration, we need to send our updated
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
#         config = EherkenningConfiguration.get_solo()
#         config.want_assertions_encrypted = True
#         config.save()

# class SignicatWithUnsignedAssertionsTests(SignicatEHerkenningIntegrationTests):
#     """These pass, but Signicat signs assertions, because it will follow
#     the metadata we uploaded previously, which wanted assertions signed.
#
#     Our SAML metadata discovery url is unreachable...
#     https://localhost:8000/discovery/digid-eherkenning/eherkenning
#
#     I don't know if this is used in a live, non-testing environment.
#     """
#
#
#     @classmethod
#     def setUpTestData(cls):
#         super().setUpTestData()
#
#         config = EherkenningConfiguration.get_solo()
#         config.want_assertions_signed = False
#         config.save()

# Same same, but different
# class SignicatWithSingnedAndEncryptedAssertionsTests(SignicatEHerkenningIntegrationTests):
#     @classmethod
#     def setUpTestData(cls):
#         super().setUpTestData()
#
#         config = EherkenningConfiguration.get_solo()
#         config.want_assertions_signed = True
#         config.want_assertions_encrypted = True
#         config.save()


# Helper functions

# poor person's enum.StrEnum
type Method = Literal["get", "post"]
type Response = TemplateResponse | requests.Response


def _parse_form(response: Response) -> tuple[Method, str, dict[str, str]]:
    "Extract method, action URL and form values from html content"
    form = WTForm(None, response.content)
    url = form.action or response.url
    assert url, f"No url found in {form}"
    method = form.method
    assert method in ("get", "post")
    return method, url, dict(form.submit_fields())
