from django.http import HttpRequest
from django.test import RequestFactory, TestCase

from mozilla_django_oidc_db.registry import register as registry
from mozilla_django_oidc_db.views import (
    _RETURN_URL_SESSION_KEY,
)

from openforms.forms.tests.factories import FormFactory
from openforms.utils.tests.keycloak import mock_get_random_string, mock_oidc_client

from .....tests.factories import AttributeGroupFactory
from .....tests.utils import URLsHelper
from ...config import YiviOptions
from ...constants import PLUGIN_ID as YIVI_PLUGIN_ID
from ...oidc_plugins.constants import OIDC_YIVI_IDENTIFIER


class ProcessClaimsYiviTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        cls.plugin = registry[OIDC_YIVI_IDENTIFIER]

    def _setup_form(self, options: YiviOptions) -> HttpRequest:
        form = FormFactory.create(
            authentication_backend=YIVI_PLUGIN_ID,
            authentication_backend__options=options,
        )
        url_helper = URLsHelper(form=form)

        session = self.client.session
        session[_RETURN_URL_SESSION_KEY] = url_helper.get_auth_start(
            plugin_id=YIVI_PLUGIN_ID
        )
        session.save()

        factory = RequestFactory()
        factory = factory
        request = factory.get("/irrelevant")
        request.session = session

        return request

    @mock_oidc_client(
        OIDC_YIVI_IDENTIFIER,
        overrides={
            "options.identity_settings.bsn_claim_path": ["test.attribute.bsn"],
            "options.identity_settings.bsn_loa_claim_path": ["bsn.loa"],
        },
    )
    def test_yivi_process_claims_with_dots_in_path(self):
        AttributeGroupFactory(
            name="know_attributes",
            attributes=["irma-demo.gemeente.personalData.familyname"],
        )
        request = self._setup_form(
            options={
                "authentication_options": [],
                "additional_attributes_groups": [
                    "know_attributes",
                    "know_attributes_2",
                ],
                "bsn_loa": "",
                "kvk_loa": "",
            }
        )

        claims = {
            "test.attribute.bsn": "123456782",
            "bsn.loa": "low",
            "irma-demo.gemeente.personalData.familyname": "Doe",
        }
        processed_claims = self.plugin.process_claims(request, claims)

        self.assertEqual(
            processed_claims,
            {
                "test.attribute.bsn": "123456782",
                "bsn.loa": "low",
                "additional_claims": {
                    "irma-demo.gemeente.personalData.familyname": "Doe"
                },
            },
        )

    def test_extract_additional_claims_with_known_attributes(self):
        AttributeGroupFactory(
            name="know_attributes", attributes=["firstname", "lastname"]
        )
        AttributeGroupFactory(name="know_attributes_2", attributes=["dob"])
        request = self._setup_form(
            options={
                "authentication_options": [],
                "additional_attributes_groups": [
                    "know_attributes",
                    "know_attributes_2",
                ],
                "bsn_loa": "",
                "kvk_loa": "",
            }
        )

        extracted_claims = self.plugin.extract_additional_claims(
            request, {"firstname": "bob", "lastname": "joe", "dob": "21-01-1999"}
        )
        self.assertEqual(
            extracted_claims,
            {"firstname": "bob", "lastname": "joe", "dob": "21-01-1999"},
        )

    def test_extract_additional_claims_with_unknown_attributes(self):
        request = self._setup_form(
            options={
                "authentication_options": [],
                "additional_attributes_groups": ["unknow_attributes"],
                "bsn_loa": "",
                "kvk_loa": "",
            }
        )

        extracted_claims = self.plugin.extract_additional_claims(
            request, {"firstname": "bob"}
        )

        self.assertEqual(extracted_claims, {})

    def test_extract_additional_claims_with_missing_claims(self):
        AttributeGroupFactory(
            name="know_attributes", attributes=["firstname", "lastname"]
        )
        request = self._setup_form(
            options={
                "authentication_options": [],
                "additional_attributes_groups": ["know_attributes"],
                "bsn_loa": "",
                "kvk_loa": "",
            }
        )

        extracted_claims = self.plugin.extract_additional_claims(
            request, {"firstname": "bob"}
        )

        self.assertEqual(extracted_claims, {"firstname": "bob"})

    @mock_get_random_string()
    @mock_oidc_client(
        OIDC_YIVI_IDENTIFIER,
        overrides={
            "options.identity_settings.bsn_claim_path": ["test.attribute.bsn"],
            "options.identity_settings.kvk_claim_path": ["test.attribute.kvk"],
            "options.identity_settings.pseudo_claim_path": ["test.attribute.pseudo"],
        },
    )
    def test_all_configured_additional_attributes_are_present_in_the_get_sensitive_claims(
        self,
    ):
        AttributeGroupFactory(
            name="know_attributes", attributes=["firstname", "lastname"]
        )
        AttributeGroupFactory(name="know_attributes_2", attributes=["dob"])
        request = self._setup_form(
            options={
                "authentication_options": [],
                "additional_attributes_groups": [
                    "know_attributes",
                    "know_attributes_2",
                ],
                "bsn_loa": "",
                "kvk_loa": "",
            }
        )

        sensitive_claims = self.plugin.get_sensitive_claims(request)

        self.assertEqual(
            sensitive_claims,
            [
                ["test.attribute.bsn"],
                ["test.attribute.kvk"],
                ["test.attribute.pseudo"],
                ["firstname"],
                ["lastname"],
                ["dob"],
            ],
        )
