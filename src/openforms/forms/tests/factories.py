import factory

from openforms.products.tests.factories import ProductFactory

from ..models import Form, FormDefinition, FormStep


class FormFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Form

    name = factory.Sequence(lambda n: "Form %03d" % n)
    slug = factory.Faker("word")
    active = True
    product = factory.SubFactory(ProductFactory)


class FormDefinitionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FormDefinition

    name = factory.Sequence(lambda n: "FormDefinition %03d" % n)
    slug = factory.Sequence(lambda n: f"fd-{n}")
    login_required = False
    configuration = '{"components": [{"type": "test-component"}]}'


class FormStepFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FormStep

    form = factory.SubFactory(FormFactory)
    form_definition = factory.SubFactory(FormDefinitionFactory)
