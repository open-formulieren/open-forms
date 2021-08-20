import factory

from ..models import RestAPI


class RestAPIFactory(factory.django.DjangoModelFactory):
    label = factory.Sequence(lambda n: f"API-{n}")
    api_root = factory.Sequence(lambda n: f"http://www.example{n}.com/api/v1/")

    class Meta:
        model = RestAPI
