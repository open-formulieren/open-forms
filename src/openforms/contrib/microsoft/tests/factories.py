import factory

from openforms.contrib.microsoft.models import MSGraphService


class MSGraphServiceFactory(factory.django.DjangoModelFactory):
    label = factory.Sequence(lambda n: "label-{n}")
    tenant_id = factory.Sequence(lambda n: "tenant_id-{n}")
    client_id = factory.Sequence(lambda n: "client_id-{n}")
    secret = factory.Sequence(lambda n: "secret-{n}")

    class Meta:
        model = MSGraphService
