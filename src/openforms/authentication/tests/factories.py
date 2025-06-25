import factory
from digid_eherkenning.choices import AssuranceLevels, DigiDAssuranceLevels

from ..constants import (
    ActingSubjectIdentifierType,
    AuthAttribute,
    LegalSubjectIdentifierType,
)
from ..contrib.digid.constants import DIGID_DEFAULT_LOA
from ..contrib.yivi_oidc.models import AttributeGroup, YiviOpenIDConnectConfig
from ..models import AuthInfo, RegistratorInfo


class AuthInfoFactory(factory.django.DjangoModelFactory):
    plugin = "digid"
    attribute = AuthAttribute.bsn
    value = "123456782"
    submission = factory.SubFactory(
        "openforms.submissions.tests.factories.SubmissionFactory"
    )
    loa = DIGID_DEFAULT_LOA

    class Meta:
        model = AuthInfo

    class Params:
        with_hashed_identifying_attributes = factory.Trait(
            _hashed_id_attrs=factory.PostGenerationMethodCall(
                "hash_identifying_attributes"
            ),
        )
        is_digid = factory.Trait(
            attribute=AuthAttribute.bsn,
            value="999991607",
            attribute_hashed=False,
            loa=DigiDAssuranceLevels.middle,
        )
        is_digid_machtigen = factory.Trait(
            attribute=AuthAttribute.bsn,
            value="999991607",
            attribute_hashed=False,
            loa=DigiDAssuranceLevels.middle,
            legal_subject_identifier_type=LegalSubjectIdentifierType.bsn,
            legal_subject_identifier_value="999999999",
            mandate_context={
                "services": [{"id": "34085d78-21aa-4481-a219-b28d7f3282fc"}],
            },
        )
        is_eh = factory.Trait(
            attribute=AuthAttribute.kvk,
            value="90002768",
            attribute_hashed=False,
            loa=AssuranceLevels.substantial,
            acting_subject_identifier_type=ActingSubjectIdentifierType.opaque,
            acting_subject_identifier_value=(
                "4B75A0EA107B3D36C82FD675B5B78CC2F181B22E33D85F2D4A5DA63452EE3018"
                "@2D8FF1EF10279BC2643F376D89835151"
            ),
        )
        is_eh_bewindvoering = factory.Trait(
            attribute=AuthAttribute.bsn,
            value="999991607",
            attribute_hashed=False,
            loa=AssuranceLevels.substantial,
            legal_subject_identifier_type=LegalSubjectIdentifierType.kvk,
            legal_subject_identifier_value="90002768",
            acting_subject_identifier_type=ActingSubjectIdentifierType.opaque,
            acting_subject_identifier_value=(
                "4B75A0EA107B3D36C82FD675B5B78CC2F181B22E33D85F2D4A5DA63452EE3018"
                "@2D8FF1EF10279BC2643F376D89835151"
            ),
            mandate_context={
                "role": "bewindvoerder",
                "services": [
                    {
                        "id": "urn:etoegang:DV:00000001002308836000:services:9113",
                        "uuid": "34085d78-21aa-4481-a219-b28d7f3282fc",
                    }
                ],
            },
        )
        is_yivi = factory.Trait(
            attribute=AuthAttribute.bsn,
            value="999991607",
            attribute_hashed=False,
            loa=DigiDAssuranceLevels.substantial,
        )


class RegistratorInfoFactory(factory.django.DjangoModelFactory):
    plugin = "org-oidc"
    attribute = AuthAttribute.employee_id
    value = "123456782"
    submission = factory.SubFactory(
        "openforms.submissions.tests.factories.SubmissionFactory"
    )

    class Meta:
        model = RegistratorInfo


class YiviOpenIDConnectConfigFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = YiviOpenIDConnectConfig
        django_get_or_create = ["id"]

    id = factory.Faker("id")


class AttributeGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AttributeGroup
