from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _

from mozilla_django_oidc_db.tests.factories import OIDCProviderFactory
from mozilla_django_oidc_db.tests.mixins import OIDCMixin

from openforms.contrib.auth_oidc.tests.factories import OFOIDCClientFactory
from openforms.plugins.exceptions import InvalidPluginConfiguration

from ..plugin import EIDASCitizenPrefill, EIDASCompanyPrefill


class EIDASCitizenConfigCheckTests(OIDCMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.provider = OIDCProviderFactory.create(
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

    @override_settings(LANGUAGE_CODE="en")
    def test_no_eidas_OIDC_client_configured(self):
        plugin = EIDASCitizenPrefill(identifier="eidas")

        with self.assertRaisesMessage(
            InvalidPluginConfiguration,
            "No enabled OIDC client for eIDAS (citizen) found.",
        ):
            plugin.check_config()

    @override_settings(LANGUAGE_CODE="en")
    def test_eidas_OIDC_client_disabled(self):
        OFOIDCClientFactory.create(
            enabled=False,
            with_eidas=True,
            oidc_provider=self.provider,
        )
        plugin = EIDASCitizenPrefill(identifier="eidas")

        with self.assertRaisesMessage(
            InvalidPluginConfiguration,
            "No enabled OIDC client for eIDAS (citizen) found.",
        ):
            plugin.check_config()

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

    @override_settings(LANGUAGE_CODE="en")
    def test_eidas_OIDC_client_missing_identity_settings_options(self):
        client = OFOIDCClientFactory.create(
            enabled=True,
            with_eidas=True,
            oidc_provider=self.provider,
        )
        plugin = EIDASCitizenPrefill(identifier="eidas")

        # Sanity check; the initial config is correct
        try:
            plugin.check_config()
        except InvalidPluginConfiguration as exc:
            raise self.failureException("Config check should have passed") from exc

        # Check that multiple missing fields are reported together
        client.options["identity_settings"].update(
            {
                "legal_subject_identifier_claim_path": [],
                "legal_subject_identifier_type_claim_path": [],
            }
        )
        client.save()

        with self.assertRaisesMessage(
            InvalidPluginConfiguration,
            "The eIDAS client identity settings are missing values for the settings: "
            "legal_subject_identifier_claim_path, legal_subject_identifier_type_claim_path.",
        ):
            plugin.check_config()


class EIDASCompanyPrefillConfigCheckTests(OIDCMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.provider = OIDCProviderFactory.create(
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

    @override_settings(LANGUAGE_CODE="en")
    def test_no_eidas_company_OIDC_client_configured(self):
        plugin = EIDASCompanyPrefill(identifier="eidas_company")

        with self.assertRaisesMessage(
            InvalidPluginConfiguration,
            "No enabled OIDC client for eIDAS (company) found.",
        ):
            plugin.check_config()

    @override_settings(LANGUAGE_CODE="en")
    def test_eidas_company_OIDC_client_disabled(self):
        OFOIDCClientFactory.create(
            enabled=False,
            with_eidas_company=True,
            oidc_provider=self.provider,
        )
        plugin = EIDASCompanyPrefill(identifier="eidas_company")

        with self.assertRaisesMessage(
            InvalidPluginConfiguration,
            "No enabled OIDC client for eIDAS (company) found.",
        ):
            plugin.check_config()

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

    @override_settings(LANGUAGE_CODE="en")
    def test_eidas_company_OIDC_client_missing_identity_settings_options(self):
        plugin = EIDASCompanyPrefill(identifier="eidas_company")
        client = OFOIDCClientFactory.create(
            enabled=True,
            with_eidas_company=True,
            oidc_provider=self.provider,
        )

        # Sanity check; the initial config is correct
        try:
            plugin.check_config()
        except InvalidPluginConfiguration as exc:
            raise self.failureException("Config check should have passed") from exc

        # Check that multiple missing fields are reported together
        client.options["identity_settings"].update(
            {
                "acting_subject_first_name_claim_path": [],
                "mandate_service_id_claim_path": [],
            }
        )
        client.save()

        with self.assertRaisesMessage(
            InvalidPluginConfiguration,
            "The eIDAS client identity settings are missing values for the settings: "
            "acting_subject_first_name_claim_path, mandate_service_id_claim_path.",
        ):
            plugin.check_config()
