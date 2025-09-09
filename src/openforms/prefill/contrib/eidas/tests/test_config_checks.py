from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from mozilla_django_oidc_db.tests.factories import OIDCProviderFactory

from openforms.contrib.auth_oidc.tests.factories import OFOIDCClientFactory
from openforms.plugins.exceptions import InvalidPluginConfiguration

from ..plugin import EIDASCitizenPrefill, EIDASCompanyPrefill


class EIDASCitizenConfigCheckTests(OIDCMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.provider = OIDCProviderFactory.create(
            identifier="oidc-eidas-provider",
            oidc_op_authorization_endpoint="http://localhost/oidc/auth",
            oidc_op_token_endpoint="http://localhost/oidc/token",
            oidc_op_user_endpoint="http://localhost/oidc/userinfo",
            oidc_op_logout_endpoint="http://localhost/oidc/logout",
        )

    def test_check_config_ok(self):
        OFOIDCClientFactory.create(
            enabled=True,
            with_eidas=True,
            oidc_provider=self.provider,
        )
        plugin = EIDASCitizenPrefill(identifier="eidas")

        try:
            plugin.check_config()
        except InvalidPluginConfiguration as exc:
            raise self.failureException("Config check should have passed") from exc

    def test_no_eidas_OIDC_client_configured(self):
        plugin = EIDASCitizenPrefill(identifier="eidas")

        with self.assertRaises(InvalidPluginConfiguration) as exc:
            plugin.check_config()

        self.assertEqual(exc.exception.args[0], _("Missing OIDC client for eIDAS."))

    def test_eidas_OIDC_client_disabled(self):
        OFOIDCClientFactory.create(
            enabled=False,
            with_eidas=True,
            oidc_provider=self.provider,
        )
        plugin = EIDASCitizenPrefill(identifier="eidas")

        with self.assertRaises(InvalidPluginConfiguration) as exc:
            plugin.check_config()

        self.assertEqual(exc.exception.args[0], _("Missing OIDC client for eIDAS."))

    def test_eidas_OIDC_client_missing_identity_settings(self):
        OFOIDCClientFactory.create(
            enabled=True,
            with_eidas=True,
            oidc_provider=self.provider,
            options__identity_settings=None,
        )
        plugin = EIDASCitizenPrefill(identifier="eidas")

        # Check the config and expect a raised exception
        with self.assertRaises(InvalidPluginConfiguration) as exc:
            plugin.check_config()

        self.assertEqual(
            exc.exception.args[0],
            _("Missing OIDC client identity settings for eIDAS."),
        )

    def test_eidas_OIDC_client_missing_identity_settings_options(self):
        client = OFOIDCClientFactory.create(
            enabled=True,
            with_eidas=True,
            oidc_provider=self.provider,
        )
        plugin = EIDASCitizenPrefill(identifier="eidas")

        required_fields = (
            "legal_subject_identifier_claim_path",
            "legal_subject_identifier_type_claim_path",
            "legal_subject_first_name_claim_path",
            "legal_subject_family_name_claim_path",
            "legal_subject_date_of_birth_claim_path",
        )

        # Sanity check; the initial config is correct
        try:
            plugin.check_config()
        except InvalidPluginConfiguration as exc:
            raise self.failureException("Config check should have passed") from exc

        # Each required_field should trigger an exception, when left empty
        for field in required_fields:
            # Clear the field
            original_data = client.options["identity_settings"][field]
            client.options["identity_settings"][field] = []
            client.save()

            # Check the config and expect a raised exception
            with self.assertRaises(InvalidPluginConfiguration) as exc:
                plugin.check_config()

            self.assertEqual(
                exc.exception.args[0],
                _("Missing OIDC client identity settings for eIDAS."),
            )

            # Reset the field.
            client.options["identity_settings"][field] = original_data
            client.save()


class EIDASCompanyPrefillConfigCheckTests(OIDCMixin, TestCase):
    def setUp(self):
        self.provider = OIDCProviderFactory.create(
            identifier="oidc-eidas-company-provider",
            oidc_op_authorization_endpoint="http://localhost/oidc/auth",
            oidc_op_token_endpoint="http://localhost/oidc/token",
            oidc_op_user_endpoint="http://localhost/oidc/userinfo",
            oidc_op_logout_endpoint="http://localhost/oidc/logout",
        )

    def test_check_config_ok(self):
        OFOIDCClientFactory.create(
            enabled=True,
            with_eidas_company=True,
            oidc_provider=self.provider,
        )
        plugin = EIDASCompanyPrefill(identifier="eidas_company")

        try:
            plugin.check_config()
        except InvalidPluginConfiguration as exc:
            raise self.failureException("Config check should have passed") from exc

    def test_no_eidas_company_OIDC_client_configured(self):
        plugin = EIDASCompanyPrefill(identifier="eidas_company")

        with self.assertRaises(InvalidPluginConfiguration) as exc:
            plugin.check_config()

        self.assertEqual(
            exc.exception.args[0], _("Missing OIDC client for eIDAS Company.")
        )

    def test_eidas_company_OIDC_client_disabled(self):
        OFOIDCClientFactory.create(
            enabled=False,
            with_eidas_company=True,
            oidc_provider=self.provider,
        )
        plugin = EIDASCompanyPrefill(identifier="eidas_company")

        with self.assertRaises(InvalidPluginConfiguration) as exc:
            plugin.check_config()

        self.assertEqual(
            exc.exception.args[0], _("Missing OIDC client for eIDAS Company.")
        )

    def test_eidas_company_OIDC_client_missing_identity_settings(self):
        plugin = EIDASCompanyPrefill(identifier="eidas_company")
        OFOIDCClientFactory.create(
            enabled=True,
            with_eidas_company=True,
            oidc_provider=self.provider,
            options__identity_settings=None,
        )

        # Check the config and expect a raised exception
        with self.assertRaises(InvalidPluginConfiguration) as exc:
            plugin.check_config()

        self.assertEqual(
            exc.exception.args[0],
            _("Missing OIDC client identity settings for eIDAS Company."),
        )

    def test_eidas_company_OIDC_client_missing_identity_settings_options(self):
        plugin = EIDASCompanyPrefill(identifier="eidas_company")
        client = OFOIDCClientFactory.create(
            enabled=True,
            with_eidas_company=True,
            oidc_provider=self.provider,
        )

        required_fields = (
            "legal_subject_identifier_claim_path",
            "legal_subject_name_claim_path",
            "acting_subject_identifier_claim_path",
            "acting_subject_identifier_type_claim_path",
            "acting_subject_first_name_claim_path",
            "acting_subject_family_name_claim_path",
            "acting_subject_date_of_birth_claim_path",
            "mandate_service_id_claim_path",
        )

        # Sanity check; the initial config is correct
        try:
            plugin.check_config()
        except InvalidPluginConfiguration as exc:
            raise self.failureException("Config check should have passed") from exc

        # Each required_field should trigger an exception, when left empty
        for field in required_fields:
            # Clear the field
            original_data = client.options["identity_settings"][field]
            client.options["identity_settings"][field] = []
            client.save()

            # Check the config and expect a raised exception
            with self.assertRaises(InvalidPluginConfiguration) as exc:
                plugin.check_config()

            self.assertEqual(
                exc.exception.args[0],
                _("Missing OIDC client identity settings for eIDAS Company."),
            )

            # Reset the field.
            client.options["identity_settings"][field] = original_data
            client.save()
