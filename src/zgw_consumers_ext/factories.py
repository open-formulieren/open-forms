import factory


class UriPathFaker(factory.Faker):
    def __init__(self, **kwargs):
        super().__init__("uri_path", **kwargs)

    def generate(self, extra_kwargs=None):
        uri_path = super().generate(extra_kwargs)
        # faker generates them without trailing slash, but let's make sure this stays true
        # zgw_consumers.Service normalizes api_root to append missing trailing slashes
        assert not uri_path.endswith("/")
        return f"{uri_path}/"


class ServiceFactory(factory.django.DjangoModelFactory):
    label = factory.Sequence(lambda n: f"API-{n}")
    api_root = UriPathFaker()

    class Meta:
        model = "zgw_consumers.Service"
        django_get_or_create = ("api_root",)
