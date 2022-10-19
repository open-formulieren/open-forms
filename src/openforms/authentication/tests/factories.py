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


class RegistratorInfoFactory(factory.django.DjangoModelFactory):
    plugin = "org-oidc"
    attribute = AuthAttribute.employee_id
    value = "123456782"
    submission = factory.SubFactory(
        "openforms.submissions.tests.factories.SubmissionFactory"
    )

    class Meta:
        model = RegistratorInfo
