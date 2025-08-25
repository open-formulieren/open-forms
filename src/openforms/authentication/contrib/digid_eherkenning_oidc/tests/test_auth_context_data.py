"""
Test the authentication flow for a form.

These tests use VCR. When re-recording, making sure to:

.. code-block:: bash

    cd docker
    docker compose -f docker-compose.keycloak.yml up

to bring up a Keycloak instance.
"""

import warnings

from django.test import override_settings
from django.urls import reverse

from django_webtest import DjangoTestApp

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.tests.utils import AuthContextAssertMixin, URLsHelper
from openforms.contrib.auth_oidc.tests.factories import OFOIDCClientFactory
from openforms.forms.tests.factories import FormFactory
from openforms.submissions.models import Submission
from openforms.utils.tests.keycloak import keycloak_login

from .base import IntegrationTestsBase


class PerformLoginMixin:
    app: DjangoTestApp
    extra_environ: dict

    def _login_and_start_form(self, plugin: str, *, username: str, password: str):
        host = f"http://{self.extra_environ['HTTP_HOST']}"
        form = FormFactory.create(authentication_backend=plugin)
        url_helper = URLsHelper(form=form, host=host)
        start_url = url_helper.get_auth_start(plugin_id=plugin)
        start_response = self.app.get(start_url)
        # simulate login to Keycloak
        redirect_uri = keycloak_login(
            start_response["Location"],
            username=username,
            password=password,
            host=host,
        )
        # complete the login flow on our end
        callback_response = self.app.get(redirect_uri, auto_follow=True)
        assert callback_response.status_code == 200
        # start submission
        create_response = self.app.post_json(
            reverse("api:submission-list"),
            {
                "form": url_helper.api_resource,
                "formUrl": url_helper.frontend_start,
            },
        )
        assert create_response.status_code == 201


@override_settings(ALLOWED_HOSTS=["*"])
class DigiDAuthContextTests(
    PerformLoginMixin,
    AuthContextAssertMixin,
    IntegrationTestsBase,
):
    csrf_checks = False
    extra_environ = {
        "HTTP_HOST": "localhost:8000",
    }

    def test_record_auth_context(self):
        OFOIDCClientFactory.create(with_keycloak_provider=True, with_digid=True)

        self._login_and_start_form(
            "digid_oidc", username="testuser", password="testuser"
        )

        submission = Submission.objects.get()
        self.assertTrue(submission.is_authenticated)
        auth_context = submission.auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertEqual(auth_context["source"], "digid")
        self.assertEqual(
            auth_context["authorizee"]["legalSubject"],
            {"identifierType": "bsn", "identifier": "000000000"},
        )


@override_settings(ALLOWED_HOSTS=["*"])
class EIDASAuthContextTests(
    PerformLoginMixin, AuthContextAssertMixin, IntegrationTestsBase
):
    csrf_checks = False
    extra_environ = {
        "HTTP_HOST": "localhost:8000",
    }

    def test_record_auth_context_for_eidas_natural_person_authentication(self):
        OFOIDCClientFactory.create(with_keycloak_provider=True, with_eidas=True)

        self._login_and_start_form(
            "eidas_oidc", username="eidas-person", password="eidas-person"
        )

        submission = Submission.objects.get()
        self.assertTrue(submission.is_authenticated)
        auth_context = submission.auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertEqual(
            auth_context,
            {
                "source": "eidas",
                "levelOfAssurance": "urn:etoegang:core:assurance-class:loa2",
                "authorizee": {
                    "legalSubject": {
                        "identifierType": "bsn",
                        "identifier": "123456789",
                        "firstName": "John",
                        "familyName": "Doe",
                        "dateOfBirth": "1946-01-25",
                    },
                },
            },
        )

    def test_record_auth_context_for_eidas_natural_pseudo_person_authentication(self):
        OFOIDCClientFactory.create(with_keycloak_provider=True, with_eidas=True)

        self._login_and_start_form(
            "eidas_oidc",
            username="eidas-person-pseudo",
            password="eidas-person-pseudo",
        )

        submission = Submission.objects.get()
        self.assertTrue(submission.is_authenticated)
        self.assertEqual(submission.auth_info.attribute, AuthAttribute.pseudo)
        auth_context = submission.auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertEqual(
            auth_context,
            {
                "source": "eidas",
                "levelOfAssurance": "urn:etoegang:core:assurance-class:loa2",
                "authorizee": {
                    "legalSubject": {
                        "identifierType": "opaque",
                        "identifier": "4B75A0EA107B3D36",
                        "firstName": "John",
                        "familyName": "Doe",
                        "dateOfBirth": "1946-01-25",
                    },
                },
            },
        )

    def test_record_auth_context_for_eidas_natural_person_without_bsn_and_pseudo_claims_authentication(
        self,
    ):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eidas=True,
            options__identity_settings__legal_subject_bsn_identifier_claim_path=[
                "invalid-claim"
            ],
            options__identity_settings__legal_subject_pseudo_identifier_claim_path=[
                "invalid-claim"
            ],
        )

        self._login_and_start_form(
            "eidas_oidc", username="eidas-person", password="eidas-person"
        )

        submission = Submission.objects.get()
        self.assertFalse(submission.is_authenticated)


@override_settings(ALLOWED_HOSTS=["*"])
class EIDASCompanyAuthContextTests(
    PerformLoginMixin, AuthContextAssertMixin, IntegrationTestsBase
):
    csrf_checks = False
    extra_environ = {
        "HTTP_HOST": "localhost:8000",
    }

    def test_record_auth_context_for_eidas_company_and_acting_subject_with_bsn_authentication(
        self,
    ):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eidas_company=True,
        )

        self._login_and_start_form(
            "eidas_company_oidc", username="eidas-company", password="eidas-company"
        )

        submission = Submission.objects.get()
        self.assertTrue(submission.is_authenticated)
        auth_context = submission.auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertEqual(
            auth_context,
            {
                "source": "eidas",
                "levelOfAssurance": "urn:etoegang:core:assurance-class:loa2",
                "authorizee": {
                    "legalSubject": {
                        "identifierType": "opaque",
                        "identifier": "NL/NTR/123456789",
                        "companyName": "example company BV",
                    },
                    "actingSubject": {
                        "identifierType": "bsn",
                        "identifier": "123456789",
                        "firstName": "John",
                        "familyName": "Doe",
                        "dateOfBirth": "1946-01-25",
                    },
                },
                "mandate": {
                    "services": [
                        {"id": "urn:etoegang:DV:00000003244440010000:services:9102"}
                    ]
                },
            },
        )

    def test_record_auth_context_for_eidas_company_and_acting_subject_with_pseudo_authentication(
        self,
    ):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eidas_company=True,
        )

        self._login_and_start_form(
            "eidas_company_oidc",
            username="eidas-company-pseudo",
            password="eidas-company-pseudo",
        )

        submission = Submission.objects.get()
        self.assertTrue(submission.is_authenticated)
        auth_context = submission.auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertEqual(
            auth_context,
            {
                "source": "eidas",
                "levelOfAssurance": "urn:etoegang:core:assurance-class:loa2",
                "authorizee": {
                    "legalSubject": {
                        "identifierType": "opaque",
                        "identifier": "NL/NTR/123456789",
                        "companyName": "example company BV",
                    },
                    "actingSubject": {
                        "identifierType": "opaque",
                        "identifier": "4B75A0EA107B3D36",
                        "firstName": "John",
                        "familyName": "Doe",
                        "dateOfBirth": "1946-01-25",
                    },
                },
                "mandate": {
                    "services": [
                        {"id": "urn:etoegang:DV:00000003244440010000:services:9102"}
                    ]
                },
            },
        )

    def test_record_auth_context_for_eidas_company_without_acting_subject_bsn_and_pseudo_claims_authentication(
        self,
    ):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eidas_company=True,
            options__identity_settings__acting_subject_bsn_identifier_claim_path=[
                "invalid-claim"
            ],
            options__identity_settings__acting_subject_peseudo_identifier_claim_path=[
                "invalid-claim"
            ],
        )

        self._login_and_start_form(
            "eidas_company_oidc", username="eidas-company", password="eidas-company"
        )

        submission = Submission.objects.get()
        self.assertFalse(submission.is_authenticated)


@override_settings(ALLOWED_HOSTS=["*"])
class EHerkenningAuthContextTests(
    PerformLoginMixin,
    AuthContextAssertMixin,
    IntegrationTestsBase,
):
    csrf_checks = False
    extra_environ = {
        "HTTP_HOST": "localhost:8000",
    }

    def test_record_auth_context(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning=True,
        )

        self._login_and_start_form(
            "eherkenning_oidc", username="testuser", password="testuser"
        )

        submission = Submission.objects.get()
        self.assertTrue(submission.is_authenticated)
        auth_context = submission.auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertEqual(auth_context["source"], "eherkenning")
        self.assertEqual(
            auth_context["authorizee"]["legalSubject"],
            {"identifierType": "kvkNummer", "identifier": "12345678"},
        )
        assert "actingSubject" in auth_context["authorizee"]
        self.assertEqual(
            auth_context["authorizee"]["actingSubject"],
            {"identifierType": "opaque", "identifier": "4B75A0EA107B3D36"},
        )
        self.assertNotIn("representee", auth_context)

    def test_record_vestiging_restriction(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning=True,
            options__identity_settings__branch_number_claim_path=["vestiging"],
        )

        self._login_and_start_form(
            "eherkenning_oidc",
            username="eherkenning-vestiging",
            password="eherkenning-vestiging",
        )

        submission = Submission.objects.get()
        self.assertTrue(submission.is_authenticated)
        auth_context = submission.auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertEqual(auth_context["source"], "eherkenning")
        self.assertEqual(
            auth_context["authorizee"]["legalSubject"],
            {
                "identifierType": "kvkNummer",
                "identifier": "12345678",
                "branchNumber": "123456789012",
            },
        )


@override_settings(ALLOWED_HOSTS=["*"])
class DigiDMachtigenAuthContextTests(
    PerformLoginMixin,
    AuthContextAssertMixin,
    IntegrationTestsBase,
):
    csrf_checks = False
    extra_environ = {
        "HTTP_HOST": "localhost:8000",
    }

    def test_record_auth_context(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_digid_machtigen=True,
        )

        self._login_and_start_form(
            "digid_machtigen_oidc",
            username="digid-machtigen",
            password="digid-machtigen",
        )

        submission = Submission.objects.get()
        self.assertTrue(submission.is_authenticated)
        auth_context = submission.auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertEqual(auth_context["source"], "digid")
        assert "representee" in auth_context
        self.assertEqual(
            auth_context["representee"],
            {"identifierType": "bsn", "identifier": "000000000"},
        )
        self.assertEqual(
            auth_context["authorizee"]["legalSubject"],
            {"identifierType": "bsn", "identifier": "999999999"},
        )

    def test_new_required_claims_are_backwards_compatible(self):
        """
        Test that the legacy configuration without additional claims still works.

        The extra authentication context (metadata) is required in the new flow, but
        this data was not extracted and/or provided before, so existing incomplete
        infrastructure should not break existing forms. At worst, we send non-compliant
        data to the registration backend/our own database, but that should not have
        runtime implications.
        """
        warnings.warn(
            "Legacy behaviour will be removed in Open Forms 4.0",
            DeprecationWarning,
            stacklevel=2,
        )
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_digid_machtigen=True,
            options__identity_settings__mandate_service_id_claim_path=[
                "required-but-absent-claim"
            ],
        )

        self._login_and_start_form(
            "digid_machtigen_oidc",
            username="digid-machtigen",
            password="digid-machtigen",
        )

        submission = Submission.objects.get()
        self.assertTrue(submission.is_authenticated)
        auth_context = submission.auth_info.to_auth_context_data()
        # it is NOT valid according to the JSON schema (!) due to the missing service
        # ID claim
        self.assertEqual(auth_context["source"], "digid")
        assert "representee" in auth_context
        self.assertEqual(
            auth_context["representee"],
            {"identifierType": "bsn", "identifier": "000000000"},
        )
        self.assertEqual(
            auth_context["authorizee"]["legalSubject"],
            {"identifierType": "bsn", "identifier": "999999999"},
        )


@override_settings(ALLOWED_HOSTS=["*"])
class EHerkenningBewindvoeringAuthContextTests(
    PerformLoginMixin,
    AuthContextAssertMixin,
    IntegrationTestsBase,
):
    csrf_checks = False
    extra_environ = {
        "HTTP_HOST": "localhost:8000",
    }

    def test_record_auth_context(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning_bewindvoering=True,
        )

        self._login_and_start_form(
            "eherkenning_bewindvoering_oidc",
            username="eherkenning-bewindvoering",
            password="eherkenning-bewindvoering",
        )

        submission = Submission.objects.get()
        self.assertTrue(submission.is_authenticated)
        auth_context = submission.auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertEqual(auth_context["source"], "eherkenning")
        assert "representee" in auth_context
        self.assertEqual(
            auth_context["representee"],
            {"identifierType": "bsn", "identifier": "000000000"},
        )
        self.assertEqual(
            auth_context["authorizee"]["legalSubject"],
            {"identifierType": "kvkNummer", "identifier": "12345678"},
        )
        assert "actingSubject" in auth_context["authorizee"]
        self.assertEqual(
            auth_context["authorizee"]["actingSubject"],
            {"identifierType": "opaque", "identifier": "4B75A0EA107B3D36"},
        )
        self.assertEqual(
            auth_context["mandate"],
            {
                "role": "bewindvoerder",
                "services": [
                    {
                        "id": "urn:etoegang:DV:00000001002308836000:services:9113",
                        "uuid": "81216fa4-80a1-4686-a8ac-5c8e5c030c93",
                    }
                ],
            },
        )

    def test_new_required_claims_are_backwards_compatible(self):
        """
        Test that the legacy configuration without additional claims still works.

        The extra authentication context (metadata) is required in the new flow, but
        this data was not extracted and/or provided before, so existing incomplete
        infrastructure should not break existing forms. At worst, we send non-compliant
        data to the registration backend/our own database, but that should not have
        runtime implications.
        """
        warnings.warn(
            "Legacy behaviour will be removed in Open Forms 4.0",
            DeprecationWarning,
            stacklevel=2,
        )
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning_bewindvoering=True,
            options__identity_settings__mandate_service_id_claim_path=[
                "required-but-absent-claim1"
            ],
            options__identity_settings__mandate_service_uuid_claim_path=[
                "required-but-absent-claim2"
            ],
        )

        self._login_and_start_form(
            "eherkenning_bewindvoering_oidc",
            username="eherkenning-bewindvoering",
            password="eherkenning-bewindvoering",
        )

        submission = Submission.objects.get()
        self.assertTrue(submission.is_authenticated)
        auth_context = submission.auth_info.to_auth_context_data()
        # it is NOT valid according to the JSON schema (!) due to the missing service
        # ID claim
        self.assertEqual(auth_context["source"], "eherkenning")
        assert "representee" in auth_context
        self.assertEqual(
            auth_context["representee"],
            {"identifierType": "bsn", "identifier": "000000000"},
        )
        self.assertEqual(
            auth_context["authorizee"]["legalSubject"],
            {"identifierType": "kvkNummer", "identifier": "12345678"},
        )
        assert "actingSubject" in auth_context["authorizee"]
        self.assertEqual(
            auth_context["authorizee"]["actingSubject"],
            {"identifierType": "opaque", "identifier": "4B75A0EA107B3D36"},
        )
        self.assertEqual(
            auth_context["mandate"],
            {"role": "bewindvoerder", "services": []},
        )

    def test_record_vestiging_restriction(self):
        OFOIDCClientFactory.create(
            with_keycloak_provider=True,
            with_eherkenning_bewindvoering=True,
            options__identity_settings__branch_number_claim_path=["vestiging"],
            options__identity_settings__legal_subject_claim_path=["legalSubjectID"],
        )

        self._login_and_start_form(
            "eherkenning_bewindvoering_oidc",
            username="eherkenning-vestiging",
            password="eherkenning-vestiging",
        )

        submission = Submission.objects.get()
        self.assertTrue(submission.is_authenticated)
        auth_context = submission.auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertEqual(auth_context["source"], "eherkenning")
        self.assertEqual(
            auth_context["authorizee"]["legalSubject"],
            {
                "identifierType": "kvkNummer",
                "identifier": "12345678",
                "branchNumber": "123456789012",
            },
        )
