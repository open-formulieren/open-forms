from unittest.mock import MagicMock, patch

from django.test import TransactionTestCase

from privates.test import temp_private_root

from openforms.authentication.service import AuthAttribute
from openforms.authentication.utils import store_auth_details, store_registrator_details
from openforms.config.models import GlobalConfiguration
from openforms.prefill.contrib.haalcentraal_brp.plugin import PLUGIN_IDENTIFIER
from openforms.prefill.service import prefill_variables
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.typing import JSONValue
from openforms.utils.tests.vcr import OFVCRMixin

from ..models import BRPPersonenRequestOptions
from .factories import HaalCentraalConfigFactory

COMPONENTS = [
    {
        "key": "bsn",
        "type": "textfield",
        "label": "BSN",
        "prefill": {
            "plugin": PLUGIN_IDENTIFIER,
            "attribute": "burgerservicenummer",
        },
        "multiple": False,
    },
    {
        "key": "address",
        "type": "textfield",
        "label": "Address",
        "prefill": {
            "plugin": PLUGIN_IDENTIFIER,
            "attribute": "adressering",
        },
        "multiple": False,
    },
]


@temp_private_root()
class BRPIntegrationTest(OFVCRMixin, TransactionTestCase):
    """Run full integration tests against a real API instance.

    These tests ensure the correct behaviour of our implementation using a real API as reference. HTTP
    traffic is recorded using VCR and we are making use of the prefill feature, although any other feature
    making use of the BRP API could have been used.
    """

    def setUp(self) -> None:
        super().setUp()

        global_config = GlobalConfiguration(organization_oin="00000003273229750000")

        global_config_patcher = patch(
            "openforms.contrib.haal_centraal.clients.GlobalConfiguration.get_solo",
            return_value=global_config,
        )
        global_config_patcher.start()
        self.addCleanup(global_config_patcher.stop)

        self.submission = SubmissionFactory.from_components(components_list=COMPONENTS)

        store_auth_details(
            submission=self.submission,
            form_auth={
                "attribute": AuthAttribute.bsn,
                "plugin": "demo",
                "value": "999990421",
            },
        )
        store_registrator_details(
            submission=self.submission,
            registrator_auth={
                "attribute": AuthAttribute.employee_id,
                "plugin": "dummy",
                "value": "SAP001",
            },
        )

    def _get_vcr_kwargs(self, **kwargs):
        kwargs = super()._get_vcr_kwargs(**kwargs)
        kwargs["filter_headers"] = ["x-api-key"]
        return kwargs

    def assertPrefillVariableValues(self, value: JSONValue) -> None:
        self.assertEqual(
            value,
            {
                "aanhef": "Geachte heer Holthuizen",
                "aanschrijfwijze": {"naam": "A.H. Holthuizen"},
                "gebruikInLopendeTekst": "de heer Holthuizen",
                "adresregel1": "Nieuwe Parklaan 58",
                "adresregel2": "2597 LD  'S-GRAVENHAGE",
            },
        )

    @patch(
        "openforms.contrib.haal_centraal.clients.HaalCentraalConfig.get_solo",
        return_value=HaalCentraalConfigFactory.build(
            default_brp_personen_purpose_limitation_header_value="BRPACT-AanschrijvenZakelijkGerechtigde",
            default_brp_personen_processing_header_value="Financiele administratie@Correspondentie factuur",
        ),
    )
    def test_brp_integration_prefill_default_headers(self, m: MagicMock) -> None:
        service = m.return_value.brp_personen_service
        # certificate instances need to be saved so that they get a correct path
        # (see https://forum.djangoproject.com/t/7533/)
        if service.client_certificate and service.server_certificate:
            service.client_certificate.save()
            service.server_certificate.save()

        prefill_variables(submission=self.submission)
        state = self.submission.load_submission_value_variables_state()

        self.assertPrefillVariableValues(state.variables["address"].value)

    @patch(
        "openforms.contrib.haal_centraal.clients.HaalCentraalConfig.get_solo",
        return_value=HaalCentraalConfigFactory.build(
            default_brp_personen_purpose_limitation_header_value="",
            default_brp_personen_processing_header_value="",
        ),
    )
    def test_brp_integration_prefill(self, m: MagicMock) -> None:
        service = m.return_value.brp_personen_service
        # certificate instances need to be saved so that they get a correct path
        # (see https://forum.djangoproject.com/t/7533/)
        if service.client_certificate and service.server_certificate:
            service.client_certificate.save()
            service.server_certificate.save()

        BRPPersonenRequestOptions.objects.create(
            form=self.submission.form,
            brp_personen_purpose_limitation_header_value="BRPACT-AanschrijvenZakelijkGerechtigde",
            brp_personen_processing_header_value="Financiele administratie@Correspondentie factuur",
        )

        prefill_variables(submission=self.submission)
        state = self.submission.load_submission_value_variables_state()

        self.assertPrefillVariableValues(state.variables["address"].value)
