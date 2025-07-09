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
from openforms.forms.tests.factories import FormFactory
from openforms.submissions.models import Submission
from openforms.utils.tests.keycloak import keycloak_login

from .base import (
    IntegrationTestsBase,
    mock_digid_config,
    mock_digid_machtigen_config,
    mock_eherkenning_bewindvoering_config,
    mock_eherkenning_config,
    mock_eidas_company_config,
    mock_eidas_config,
)


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
    PerformLoginMixin, AuthContextAssertMixin, IntegrationTestsBase
):
    csrf_checks = False
    extra_environ = {
        "HTTP_HOST": "localhost:8000",
    }

    @mock_digid_config()
    def test_record_auth_context(self):
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

    @mock_eidas_config()
    def test_record_auth_context_for_eidas_natural_person_authentication(self):
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
                "levelOfAssurance": "low",
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

    @mock_eidas_config()
    def test_record_auth_context_for_eidas_natural_national_person_authentication(self):
        self._login_and_start_form(
            "eidas_oidc",
            username="eidas-person-national",
            password="eidas-person-national",
        )

        submission = Submission.objects.get()
        self.assertTrue(submission.is_authenticated)
        self.assertEqual(submission.auth_info.attribute, AuthAttribute.national_id)
        auth_context = submission.auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertEqual(
            auth_context,
            {
                "source": "eidas",
                "levelOfAssurance": "low",
                "authorizee": {
                    "legalSubject": {
                        "identifierType": "nationalID",
                        "identifier": "070770-905D",
                        "firstName": "John",
                        "familyName": "Doe",
                        "dateOfBirth": "1946-01-25",
                    },
                },
            },
        )

    @mock_eidas_config(legal_subject_identifier_type_claim=["invalid-claim"])
    def test_record_auth_context_for_eidas_natural_person_authentication_with_missing_legal_subject_identifier_type_claim(
        self,
    ):
        self._login_and_start_form(
            "eidas_oidc", username="eidas-person", password="eidas-person"
        )

        submission = Submission.objects.get()
        self.assertTrue(submission.is_authenticated)
        # Assert that, in the absense of the ``legal_subject_identifier_type_claim``,
        # ``AuthAttribute.pseudo`` was set as the ``auth_info.attribute``.
        self.assertEqual(submission.auth_info.attribute, AuthAttribute.pseudo)
        auth_context = submission.auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        self.assertEqual(
            auth_context,
            {
                "source": "eidas",
                "levelOfAssurance": "low",
                "authorizee": {
                    "legalSubject": {
                        "identifierType": "opaque",
                        "identifier": "123456789",
                        "firstName": "John",
                        "familyName": "Doe",
                        "dateOfBirth": "1946-01-25",
                    },
                },
            },
        )


@override_settings(ALLOWED_HOSTS=["*"])
class EIDASCompanyAuthContextTests(
    PerformLoginMixin, AuthContextAssertMixin, IntegrationTestsBase
):
    csrf_checks = False
    extra_environ = {
        "HTTP_HOST": "localhost:8000",
    }

    @mock_eidas_company_config()
    def test_record_auth_context_for_eidas_company_authentication(self):
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
                "levelOfAssurance": "low",
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

    @mock_eidas_company_config(acting_subject_identifier_type_claim=["invalid-claim"])
    def test_record_auth_context_for_eidas_company_authentication_with_missing_acting_subject_identifier_type_claim(
        self,
    ):
        self._login_and_start_form(
            "eidas_company_oidc", username="eidas-company", password="eidas-company"
        )

        submission = Submission.objects.get()
        self.assertTrue(submission.is_authenticated)
        # Assert that, in the absense of the ``acting_subject_identifier_type_claim``,
        # ``AuthAttribute.pseudo`` was set as the ``acting_subject_identifier_type``.
        self.assertEqual(
            submission.auth_info.acting_subject_identifier_type, AuthAttribute.pseudo
        )
        auth_context = submission.auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
        # Without the `person_identifier_type_claim`, expect the actingSubject
        # identifierType to be `"opaque"`
        self.assertEqual(
            auth_context,
            {
                "source": "eidas",
                "levelOfAssurance": "low",
                "authorizee": {
                    "legalSubject": {
                        "identifierType": "opaque",
                        "identifier": "NL/NTR/123456789",
                        "companyName": "example company BV",
                    },
                    "actingSubject": {
                        "identifierType": "opaque",
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


@override_settings(ALLOWED_HOSTS=["*"])
class EHerkenningAuthContextTests(
    PerformLoginMixin, AuthContextAssertMixin, IntegrationTestsBase
):
    csrf_checks = False
    extra_environ = {
        "HTTP_HOST": "localhost:8000",
    }

    @mock_eherkenning_config()
    def test_record_auth_context(self):
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

    @mock_eherkenning_config(branch_number_claim=["vestiging"])
    def test_record_vestiging_restriction(self):
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
    PerformLoginMixin, AuthContextAssertMixin, IntegrationTestsBase
):
    csrf_checks = False
    extra_environ = {
        "HTTP_HOST": "localhost:8000",
    }

    @mock_digid_machtigen_config()
    def test_record_auth_context(self):
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

    @mock_digid_machtigen_config(mandate_service_id_claim=["required-but-absent-claim"])
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
    PerformLoginMixin, AuthContextAssertMixin, IntegrationTestsBase
):
    csrf_checks = False
    extra_environ = {
        "HTTP_HOST": "localhost:8000",
    }

    @mock_eherkenning_bewindvoering_config()
    def test_record_auth_context(self):
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

    @mock_eherkenning_bewindvoering_config(
        mandate_service_id_claim=["required-but-absent-claim1"],
        mandate_service_uuid_claim=["required-but-absent-claim2"],
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

    @mock_eherkenning_bewindvoering_config(branch_number_claim=["vestiging"])
    def test_record_vestiging_restriction(self):
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
