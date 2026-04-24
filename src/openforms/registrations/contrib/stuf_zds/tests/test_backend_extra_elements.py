from decimal import Decimal
from pathlib import Path

from lxml import etree
from privates.test import temp_private_root

from openforms.payments.constants import PaymentStatus
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.submissions.tests.factories import (
    SubmissionFactory,
)
from openforms.utils.tests.vcr import OFVCRMixin
from stuf.stuf_zds.models import StufZDSConfig
from stuf.stuf_zds.tests import StUFZDSTestBase
from stuf.tests.factories import StufServiceFactory

from ....constants import RegistrationAttribute
from ..options import default_variables_mapping
from ..plugin import PLUGIN_IDENTIFIER, StufZDSRegistration
from ..typing import RegistrationOptions

TESTS_DIR = Path(__file__).parent.resolve()


@temp_private_root()
class StufZDSExtraElementsTests(OFVCRMixin, StUFZDSTestBase):
    VCR_TEST_FILES = TESTS_DIR / "files"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.zds_service = StufServiceFactory.create(
            soap_service__url="http://localhost:82/stuf-zds"
        )
        config = StufZDSConfig.get_solo()
        config.service = cls.zds_service
        config.save()
        cls.addClassCleanup(StufZDSConfig.clear_cache)

    def test_register_with_variables_mapping_initiator(self):
        options: RegistrationOptions = {
            "zds_zaaktype_code": "foo",
            "zds_documenttype_omschrijving_inzending": "foo",
            "zds_zaakdoc_vertrouwelijkheid": "GEHEIM",
            "variables_mapping": default_variables_mapping(),
            "variables_mapping_initiator": [
                {
                    "form_variable": "phone",
                    "stuf_name": "pv_afwijkendtelefoon",
                },
                {
                    "form_variable": "email",
                    "stuf_name": "pv_emailafwijkend",
                },
            ],
        }
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "name",
                    "type": "textfield",
                    "label": "Name",
                    "registration": {
                        "attribute": RegistrationAttribute.initiator_voornamen,
                    },
                },
                {
                    "key": "phone",
                    "type": "phoneNumber",
                    "label": "Phone",
                },
                {
                    "key": "email",
                    "type": "email",
                    "label": "Email",
                },
            ],
            form__name="my-form",
            bsn="111222333",
            submitted_data={
                "name": "John",
                "phone": "0612345678",
                "email": "john@smith.com",
            },
            language_code="en",
            public_registration_reference="OF-1234",
            registration_result={"zaak": "1234"},
        )
        # can't pass this as part of `SubmissionFactory.from_components`
        submission.price = Decimal("40.00")
        submission.save()
        SubmissionPaymentFactory.create(
            submission=submission,
            amount=Decimal("25.00"),
            public_order_id="foo",
            status=PaymentStatus.completed,
            provider_payment_id="123456",
        )
        plugin = StufZDSRegistration(PLUGIN_IDENTIFIER)

        plugin.register_submission(submission, options)

        stuf_request = self.cassette.requests[0]
        xml_doc = etree.fromstring(stuf_request.body)
        self.assertSoapXMLCommon(xml_doc)

        # check that we still have payment attributes on the Object level
        expected_items = {
            "payment_completed": "true",
            "payment_amount": "40.0",
            "payment_public_order_ids.0": "foo",
            "provider_payment_ids.0": "123456",
        }
        for name, value in expected_items.items():
            with self.subTest(extra_element=name, value=value):
                self.assertXPathEqual(
                    xml_doc,
                    f"//zkn:object/stuf:extraElementen/stuf:extraElement[@naam='{name}']",
                    value,
                )

        # check extra attributes on the Initiator level
        expected_items = {
            "pv_afwijkendtelefoon": "0612345678",
            "pv_emailafwijkend": "john@smith.com",
        }
        for name, value in expected_items.items():
            with self.subTest(extra_element=name, value=value):
                self.assertXPathEqual(
                    xml_doc,
                    f"//zkn:object/zkn:heeftAlsInitiator/stuf:extraElementen/stuf:extraElement[@naam='{name}']",
                    value,
                )
