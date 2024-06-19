"""
The authentication context describes details of an authentication.

A data model is proposed in github.com/maykinmedia/authentication-context-schemas (
private repository), with a JSON schema to specify and validate it. Vendors are free
to store and exchange this data, as long as it can be reconstructed into an object
that passes validation.

The schema used in these tests is taken from the proposal above. It will be made public
at some point.
"""

import json
from pathlib import Path

from django.test import SimpleTestCase

from digid_eherkenning.choices import DigiDAssuranceLevels
from jsonschema import ValidationError, Validator
from jsonschema.validators import validator_for

from openforms.submissions.tests.factories import SubmissionFactory

from ..constants import (
    ActingSubjectIdentifierType,
    AuthAttribute,
    LegalSubjectIdentifierType,
)
from ..models import AuthInfo

SCHEMA_FILE = Path(__file__).parent.resolve() / "auth_context_schema.json"


def _get_validator() -> Validator:
    with SCHEMA_FILE.open("r") as infile:
        schema = json.load(infile)
    return validator_for(schema)(schema)


validator = _get_validator()


class AuthContextDataTests(SimpleTestCase):

    def assertValidContext(self, context):
        try:
            validator.validate(context)
        except ValidationError as exc:
            raise self.failureException(
                "Context is not valid according to schema"
            ) from exc

    def test_plain_digid_auth(self):
        auth_info = AuthInfo(
            submission=SubmissionFactory.build(),
            plugin="dummy",
            attribute=AuthAttribute.bsn,
            value="999991607",
            attribute_hashed=False,
            loa=DigiDAssuranceLevels.middle,
            legal_subject_identifier_type="",
            legal_subject_identifier_value="",
        )

        auth_context = auth_info.to_auth_context_data()

        self.assertValidContext(auth_context)
