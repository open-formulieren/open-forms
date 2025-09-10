from django.test import TransactionTestCase

from privates.test import temp_private_root

from openforms.authentication.service import AuthAttribute
from openforms.forms.tests.factories import FormVariableFactory
from openforms.prefill.service import prefill_variables
from openforms.submissions.tests.factories import SubmissionFactory

from ..constants import PLUGIN_IDENTIFIER
from ..plugin import YiviPrefill


@temp_private_root()
class YiviPrefillTests(TransactionTestCase):
    def test_get_prefill_values(self):
        plugin = YiviPrefill(identifier=PLUGIN_IDENTIFIER)

        submission = SubmissionFactory.create(
            auth_info__value="111222333",
            auth_info__plugin="yivi_oidc",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__additional_claims={
                "irma-demo_gemeente_personalData_firstname": "Joe",
            },
        )

        values = plugin.get_prefill_values(
            submission,
            [
                "value",
                "additional_claims.irma-demo_gemeente_personalData_firstname",
            ],
        )

        expected = {
            "value": "111222333",
            "additional_claims.irma-demo_gemeente_personalData_firstname": "Joe",
        }
        self.assertEqual(values, expected)

    def test_get_prefill_values_with_unknown_attribute(self):
        plugin = YiviPrefill(identifier=PLUGIN_IDENTIFIER)

        submission = SubmissionFactory.create(
            auth_info__value="111222333",
            auth_info__plugin="yivi_oidc",
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__additional_claims={
                "irma-demo_gemeente_personalData_firstname": "Joe",
            },
        )

        values = plugin.get_prefill_values(
            submission,
            [
                "value",
                "additional_claims.irma-demo_gemeente_personalData_firstname",
                "additional_claims.irma-demo_gemeente_personalData_over18",
            ],
        )

        # Expect the unknown attribute not to be resolved
        expected = {
            "value": "111222333",
            "additional_claims.irma-demo_gemeente_personalData_firstname": "Joe",
        }
        self.assertEqual(values, expected)

    def test_get_prefill_values_not_authenticated(self):
        submission = SubmissionFactory.create()
        assert not submission.is_authenticated
        FormVariableFactory.create(
            key="skipped_prefill",
            form=submission.form,
            user_defined=True,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_attribute="additional_claims.irma-demo_gemeente_personalData_firstname",
        )

        prefill_variables(submission=submission)
        state = submission.load_submission_value_variables_state()

        # assert that nothing was prefilled
        values = state.get_data()
        self.assertEqual(values, {})

    def test_get_prefill_values_authenticated_with_wrong_auth_plugin(self):
        submission = SubmissionFactory.create(
            auth_info__value="111222333",
            auth_info__plugin="digid_oidc",
            auth_info__attribute=AuthAttribute.bsn,
        )
        assert submission.is_authenticated
        FormVariableFactory.create(
            key="skipped_prefill",
            form=submission.form,
            user_defined=True,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_attribute="value",
        )

        prefill_variables(submission=submission)
        state = submission.load_submission_value_variables_state()

        # assert that nothing was prefilled
        values = state.get_data()
        self.assertEqual(values, {})
