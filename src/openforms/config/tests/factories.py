import factory


class RichTextColorFactory(factory.django.DjangoModelFactory):
    color = factory.Faker("hex_color")
    label = factory.Faker("color_name")

    class Meta:
        model = "config.RichTextColor"


class ThemeFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("bs")

    class Meta:
        model = "config.Theme"


class MapTileLayerFactory(factory.django.DjangoModelFactory):
    identifier = factory.Sequence(lambda n: f"map-tile-layer-{n}")
    url = factory.Sequence(lambda n: f"http://example-{n}.com")
    label = factory.Faker("word")

    class Meta:
        model = "config.MapTileLayer"


class MapWMSTileLayerFactory(factory.django.DjangoModelFactory):
    url = factory.Sequence(lambda n: f"http://example-{n}.com")
    name = factory.Faker("word")

    class Meta:
        model = "config.MapWMSTileLayer"
