from pathlib import Path
from unittest.mock import patch

from django.test import TestCase

from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.contrib.klantinteracties.models import KlantinteractiesConfig
from openforms.forms.tests.factories import FormVariableFactory
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.vcr import OFVCRMixin
from openforms.variables.constants import FormVariableDataTypes

from ....service import prefill_variables
from ..plugin import PLUGIN_IDENTIFIER, klantinteractiesPlugin


class KlantinteractiesPluginTests(OFVCRMixin, TestCase):
    VCR_TEST_FILES = Path(__file__).parent / "files"

    def setUp(self):
        super().setUp()

        config = KlantinteractiesConfig(
            service=ServiceFactory.build(
                api_root="http://localhost:8005/klantinteracties/api/v1/",
                api_type=APITypes.kc,
                header_key="Authorization",
                header_value="Token 9b17346dbb9493f967e6653bbcdb03ac2f7009fa",
                auth_type=AuthTypes.api_key,
            )
        )
        patcher = patch(
            "openforms.contrib.klantinteracties.client.KlantinteractiesConfig.get_solo",
            return_value=config,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_prefill_values_found(self):
        submission = SubmissionFactory.create(auth_info__value="123456782")
        assert submission.is_authenticated

        FormVariableFactory.create(
            key="profile_prefill",
            form=submission.form,
            user_defined=True,
            data_type=FormVariableDataTypes.object,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "email": True,
                "phone_number": True,
            },
        )

        prefill_variables(submission=submission)
        state = submission.load_submission_value_variables_state()

        expected = {
            "emails": [
                "someemail@example.org",
                "devilkiller@example.org",
                "john.smith@gmail.com",
            ],
            "preferred_email": "john.smith@gmail.com",
            "phone_numbers": ["0687654321", "0612345678"],
            "preferred_phone_number": "0612345678",
        }
        self.assertEqual(state.variables["profile_prefill"].value, expected)

    def test_prefill_values_not_found(self):
        submission = SubmissionFactory.create(auth_info__value="123456780")
        assert submission.is_authenticated
        FormVariableFactory.create(
            key="profile_prefill",
            form=submission.form,
            user_defined=True,
            data_type=FormVariableDataTypes.object,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "email": True,
                "phone_number": True,
            },
        )

        prefill_variables(submission=submission)
        state = submission.load_submission_value_variables_state()

        self.assertEqual(state.variables["profile_prefill"].value, {})

    def test_prefill_values_not_configured(self):
        submission = SubmissionFactory.create(auth_info__value="123456782")
        FormVariableFactory.create(
            key="profile_prefill",
            form=submission.form,
            user_defined=True,
            data_type=FormVariableDataTypes.object,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options={
                "email": True,
                "phone_number": True,
            },
        )
        config_empty = KlantinteractiesConfig(service=None)

        with patch(
            "openforms.contrib.klantinteracties.client.KlantinteractiesConfig.get_solo",
            return_value=config_empty,
        ):
            prefill_variables(submission=submission)
            state = submission.load_submission_value_variables_state()

        self.assertEqual(state.variables["profile_prefill"].value, {})

    def test_config_invalid(self):
        plugin = klantinteractiesPlugin("klantinteracties-invalid")
        config_invalid = KlantinteractiesConfig(
            service=ServiceFactory.build(
                api_root="http://localhost:8005/klantinteracties/api/v1/invalid",
                api_type=APITypes.kc,
                header_key="Authorization",
                header_value="Token INVALID",
                auth_type=AuthTypes.api_key,
            )
        )
        with patch(
            "openforms.contrib.klantinteracties.client.KlantinteractiesConfig.get_solo",
            return_value=config_invalid,
        ):
            with self.assertRaises(InvalidPluginConfiguration):
                plugin.check_config()
