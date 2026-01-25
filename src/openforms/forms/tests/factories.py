import random

import factory.fuzzy

from openforms.authentication.registry import register as authentication_registry
from openforms.forms.constants import LogicActionTypes
from openforms.products.tests.factories import ProductFactory
from openforms.registrations.registry import register as registration_registry
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources

from ..models import Form, FormDefinition, FormStep, FormVariable
from ..utils import form_to_json


def authentication_plugins():
    return [p.identifier for p in authentication_registry.iter_enabled_plugins()]


def random_registration_plugin():
    # TODO: remove database/cache IO on GlobalConfiguration here?
    return random.choice(
        [p.identifier for p in registration_registry.iter_enabled_plugins()]
    )


class FormFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f"Form {n:03d}")
    slug = factory.Faker("word")
    active = True
    product = factory.SubFactory(ProductFactory)
    category = factory.SubFactory("openforms.forms.tests.factories.CategoryFactory")
    payment_backend = ""
    # factory-boy ignores attributes starting with an underscore so we'll use Meta.rename
    deleted_ = False

    class Meta:
        model = "forms.Form"
        rename = {"deleted_": "_is_deleted"}

    class Params:
        generate_minimal_setup = factory.Trait(
            formstep=factory.RelatedFactory(
                "openforms.forms.tests.factories.FormStepFactory",
                factory_related_name="form",
            ),
        )
        is_appointment_form = factory.Trait(
            generate_minimal_setup=False,  # there are no form steps
            is_appointment=True,
        )
        # prevent options passed to Form() and set a default
        registration_backend_options = {}
        authentication_backend_options = {}

    @factory.lazy_attribute
    def registration_backend__options(backend_resolver):
        # Then JIT read it from the parent Params
        # I've seen self modifying assembly, cpp/c++ template hacks
        # but this API... 🤯
        return backend_resolver.factory_parent.registration_backend_options

    @factory.post_generation
    def registration_backend(form, create, extracted, **kwargs):
        if extracted is None:
            return
        (
            FormRegistrationBackendFactory.create
            if create
            # Does build even make sense? Is it just to keep the garbage collector busy?
            # Let's anyway; maybe the constructor has side-effects; everything is possible.
            else FormRegistrationBackendFactory.build
        )(form=form, backend=extracted, **kwargs)

    @factory.lazy_attribute
    def authentication_backend__options(backend_resolver):
        return backend_resolver.factory_parent.authentication_backend_options

    @factory.post_generation
    def authentication_backend(form, create, extracted, **kwargs):
        if not extracted:
            return

        if not create:
            raise ValueError("You must use a create strategy")

        FormAuthenticationBackendFactory.create(form=form, backend=extracted, **kwargs)

    @factory.post_generation
    def price_logic(
        form: Form,  # pyright: ignore[reportGeneralTypeIssues]
        create,
        extracted,
        **kwargs,
    ):
        """
        Configure the form to evaluate the price using logic rules and read it from
        the respective variable.

        .. note:: submissions for the form must call
           ``openforms.submissions.utils.persist_user_defined_variables``

        .. note:: forms with price logic must have at least one step
        """
        if not (extracted or kwargs):
            return

        if not create:
            raise ValueError(
                "Price logic can only be specified with the create strategy"
            )

        form_logic = extracted or FormLogicFactory.create(
            form=form,
            json_logic_trigger=kwargs.get("json_logic_trigger", True),
            for_submission_price=True,
            price_variable=kwargs.get("price_variable", "totalPrice"),
            price_value=kwargs.get("price_value", 5.00),
            order=kwargs.get(
                "order", 1000
            ),  # should typically be one of the last rules evaluated
        )
        variable_key = form_logic.actions[0]["variable"]
        FormVariableFactory.create(form=form, for_price=True, key=variable_key)
        form.price_variable_key = variable_key
        form.save()


class FormRegistrationBackendFactory(factory.django.DjangoModelFactory):
    key = factory.Sequence(lambda n: f"backend{n}")
    name = factory.Faker("catch_phrase")
    backend = factory.LazyFunction(random_registration_plugin)
    form = factory.SubFactory(FormFactory)

    class Meta:
        model = "forms.FormRegistrationBackend"


class FormAuthenticationBackendFactory(factory.django.DjangoModelFactory):
    backend = factory.fuzzy.FuzzyChoice(lambda: authentication_plugins())
    form = factory.SubFactory(FormFactory)

    class Meta:
        model = "forms.FormAuthenticationBackend"
        django_get_or_create = ("form", "backend")


class FormDefinitionFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f"FormDefinition {n:03d}")

    slug = factory.Sequence(lambda n: f"fd-{n}")
    login_required = False
    configuration = factory.Sequence(
        lambda n: {
            "components": [
                {
                    "type": "textfield",
                    "key": f"test-key-{n}",
                    "label": f"Test label {n}",
                }
            ]
        }
    )

    class Meta:
        model = "forms.FormDefinition"

    class Params:
        is_appointment = factory.Trait(
            configuration={
                "display": "form",
                "components": [
                    {
                        "key": "product",
                        "type": "textfield",
                        "appointments": {"showProducts": True},
                        "label": "Product",
                    },
                    {
                        "key": "location",
                        "type": "textfield",
                        "appointments": {"showLocations": True},
                        "label": "Location",
                    },
                    {
                        "key": "time",
                        "type": "textfield",
                        "appointments": {"showTimes": True},
                        "label": "Time",
                    },
                    {
                        "key": "lastName",
                        "type": "textfield",
                        "appointments": {"lastName": True},
                        "label": "Last Name",
                    },
                    {
                        "key": "birthDate",
                        "type": "date",
                        "appointments": {"birthDate": True},
                        "label": "Date of Birth",
                    },
                ],
            }
        )


class FormStepFactory(factory.django.DjangoModelFactory):
    form_definition = factory.SubFactory(FormDefinitionFactory)
    form = factory.SubFactory(FormFactory)

    class Meta:
        model = "forms.FormStep"

    @classmethod
    def create(
        cls,
        **kwargs,
    ) -> FormStep:
        form_step = super().create(**kwargs)
        FormVariable.objects.synchronize_for(form_step.form_definition)
        return form_step

    @classmethod
    def _create(cls, *args, **kwargs):
        # This method is called instead of create() from the FormFactory with `generte_minimal_setup`
        form_step = super()._create(*args, **kwargs)
        FormVariable.objects.synchronize_for(form_step.form_definition)
        return form_step


class FormVersionFactory(factory.django.DjangoModelFactory):
    form = factory.SubFactory(FormFactory)
    export_blob = {}

    class Meta:
        model = "forms.FormVersion"

    @factory.post_generation
    def post(obj, create, extracted, **kwargs):
        json_form = form_to_json(obj.form.id)
        obj.export_blob = json_form
        obj.save()


class FormLogicFactory(factory.django.DjangoModelFactory):
    form = factory.SubFactory(FormFactory)
    json_logic_trigger = {"==": [{"var": "test-key"}, 1]}

    class Meta:
        model = "forms.FormLogic"

    class Params:
        # generate a logic rule that sets a submission price
        for_submission_price = False
        price_variable = "totalPrice"
        price_value = 5.00  # literal value or JSON logic expression

    @factory.lazy_attribute
    def actions(self):
        if self.for_submission_price:  # type: ignore
            return [
                {
                    "variable": self.price_variable,  # type: ignore
                    "action": {
                        "type": LogicActionTypes.variable,
                        "value": self.price_value,  # type: ignore
                    },
                }
            ]
        return [
            {
                "action": {
                    "type": LogicActionTypes.set_registration_backend,
                    "value": "foo",
                },
            }
        ]


class FormVariableFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f"Variable {n:03d}")
    form = factory.SubFactory(FormFactory)
    key = factory.Faker("word")
    source = FormVariableSources.user_defined
    data_type = FormVariableDataTypes.string
    initial_value = None

    class Meta:
        model = "forms.FormVariable"

    class Params:
        user_defined = factory.Trait(
            source=FormVariableSources.user_defined,
            form_definition=None,
        )
        for_price = factory.Trait(
            name="Total price",
            key="totalPrice",
            form_definition=None,
            source=FormVariableSources.user_defined,
            data_type=FormVariableDataTypes.float,
        )

    @factory.post_generation
    def form_definition(obj, create, extracted, **kwargs):
        if obj.source == FormVariableSources.user_defined:
            return

        if extracted:
            obj.form_definition = extracted
        else:
            candidates = FormDefinition.objects.filter(formstep__form=obj.form)
            for candidate in candidates:
                for component in candidate.iter_components(recursive=True):
                    if component["key"] == obj.key:
                        obj.form_definition = candidate
                        break
            else:
                raise ValueError(
                    "Bad test data setup - no form definition definition found "
                    f"having the component key '{obj.key}'."
                )

        if create:
            obj.save()


class CategoryFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f"Category {n:03d}")

    class Meta:
        model = "forms.Category"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # defer creation to treebeard instead of fuzzing the underlying DB fields
        parent = kwargs.pop("parent", None)
        if parent is not None:
            return parent.add_child(**kwargs)
        return model_class.add_root(**kwargs)
