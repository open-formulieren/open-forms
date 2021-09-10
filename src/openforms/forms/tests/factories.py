import factory

from openforms.products.tests.factories import ProductFactory

from ..models import Form, FormDefinition, FormStep, FormVersion
from ..utils import form_to_json


class FormFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "Form %03d" % n)
    slug = factory.Faker("word")
    active = True
    product = factory.SubFactory(ProductFactory)
    payment_backend = ""
    # factory-boy ignores attributes starting with an underscore so we'll use Meta.rename
    deleted_ = False

    class Meta:
        model = Form
        rename = {"deleted_": "_is_deleted"}


class FormDefinitionFactory(factory.django.DjangoModelFactory):
    public_name = factory.Sequence(lambda n: "FormDefinition %03d" % n)

    slug = factory.Sequence(lambda n: f"fd-{n}")
    login_required = False
    configuration = {"components": [{"type": "test-component", "key": "test-key"}]}

    class Meta:
        model = FormDefinition


class FormStepFactory(factory.django.DjangoModelFactory):
    form_definition = factory.SubFactory(FormDefinitionFactory)
    form = factory.SubFactory(FormFactory)

    class Meta:
        model = FormStep


class FormVersionFactory(factory.django.DjangoModelFactory):
    form = factory.SubFactory(FormFactory)
    export_blob = {}

    class Meta:
        model = FormVersion

    @factory.post_generation
    def post(obj, create, extracted, **kwargs):
        json_form = form_to_json(obj.form.id)
        obj.export_blob = json_form
        obj.save()
