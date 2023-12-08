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
