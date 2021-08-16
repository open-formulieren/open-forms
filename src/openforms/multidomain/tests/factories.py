import factory

from ..models import Domain


class DomainFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f"Site {n}")
    url = factory.Sequence(lambda n: f"http://example-{n}.com")
    is_current = False

    class Meta:
        model = Domain
