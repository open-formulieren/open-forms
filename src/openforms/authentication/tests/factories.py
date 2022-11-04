import factory

from ..constants import AuthAttribute
from ..models import AuthInfo, RegistratorInfo


class AuthInfoFactory(factory.django.DjangoModelFactory):
    plugin = "digid"
    attribute = AuthAttribute.bsn
    value = "123456782"
    machtigen = {}
    submission = factory.SubFactory(
        "openforms.submissions.tests.factories.SubmissionFactory"
    )

    class Meta:
        model = AuthInfo

    class Params:
        with_hashed_identifying_attributes = factory.Trait(
            _hashed_id_attrs=factory.PostGenerationMethodCall(
                "hash_identifying_attributes"
            ),
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
