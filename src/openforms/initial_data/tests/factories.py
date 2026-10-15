import factory
import factory.fuzzy

from openforms.accounts.tests.factories import UserFactory
from openforms.forms.tests.factories import FormFactory

from ..constants import SupportedAuthAttributes


class InitialSubmissionDataFactory(factory.django.DjangoModelFactory):
    form = factory.SubFactory(FormFactory)
    representee_auth_attribute = factory.fuzzy.FuzzyChoice(
        choices=SupportedAuthAttributes
    )
    representee_auth_value = "XXXXXXXXX"
    ttl = factory.fuzzy.FuzzyInteger(low=1, high=24)
    owner = factory.SubFactory(UserFactory)

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = "initial_data.InitialSubmissionData"
