import factory

from openforms.products.tests.factories import ProductFactory

from ..models import Form, FormDefinition, FormStep, FormVersion
from ..utils import form_to_json


class FormFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Form
        rename = {"deleted_": "_is_deleted"}

    name = factory.Sequence(lambda n: "Form %03d" % n)
    slug = factory.Faker("word")
    active = True
    product = factory.SubFactory(ProductFactory)

    # factory-boy ignores attributes starting with an underscore so we'll use Meta.rename
    deleted_ = False


class FormDefinitionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FormDefinition

    name = factory.Sequence(lambda n: "FormDefinition %03d" % n)
    slug = factory.Sequence(lambda n: f"fd-{n}")
    login_required = False
    configuration = {"components": [{"type": "test-component", "key": "test-key"}]}


class FormStepFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FormStep

    form = factory.SubFactory(FormFactory)
    form_definition = factory.SubFactory(FormDefinitionFactory)


class FormVersionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FormVersion

    form = factory.SubFactory(FormFactory)
    export_blob = {}

    @factory.post_generation
    def post(obj, create, extracted, **kwargs):
        json_form = form_to_json(obj.form.id)
        obj.export_blob = json_form
        obj.save()
