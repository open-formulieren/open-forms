from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase
from django.utils.translation import gettext as _

from rest_framework.exceptions import ValidationError as DRFValidationError

from openforms.submissions.models import Submission
from openforms.validations.registry import Registry, StringValueSerializer


class DjangoValidator:
    is_enabled = True
    components = ("textfield",)
    value_serializer = StringValueSerializer

    def __call__(self, value, submission):
        if value != "VALID":
            raise DjangoValidationError("not VALID value")


class DRFValidator:
    is_enabled = True
    components = ("phoneNumber",)
    value_serializer = StringValueSerializer

    def __call__(self, value, submission):
        if value != "VALID":
            raise DRFValidationError("not VALID value")


class DisabledValidator:
    is_enabled = False
    components = ("textfield",)
    value_serializer = StringValueSerializer

    def __call__(self, value, submission):
        if value != "VALID":
            raise DRFValidationError("not VALID value")


def function_validator(value, submission):
    if value != "VALID":
        raise DjangoValidationError("not VALID value")


function_validator.value_serializer = StringValueSerializer


class RegistryTest(TestCase):
    def test_register_function(self):
        register = Registry()
        register("plugin", "Plugin")(DjangoValidator)
        plugin = register["plugin"]
        self.assertNotIsInstance(plugin, DjangoValidator)
        self.assertIsInstance(plugin.callable, DjangoValidator)

    def test_duplicate_identifier(self):
        register = Registry()
        register("plugin", "Plugin")(DjangoValidator)

        with self.assertRaisesMessage(
            ValueError,
            "The unique identifier 'plugin' is already present in the registry",
        ):
            register("plugin", "Plugin")(DjangoValidator)

    def test_decorator(self):
        registry = Registry()

        def decorated(value, submission):
            pass

        decorated.value_serializer = StringValueSerializer
        registry("func", verbose_name="Function")(decorated)

        wrapped = list(registry)[0]
        self.assertEqual(wrapped.identifier, "func")
        self.assertEqual(wrapped.verbose_name, "Function")
        self.assertEqual(wrapped.callable, decorated)

    def test_validate(self):
        registry = Registry()
        registry("django", "Django")(DjangoValidator)
        registry("drf", "DRF")(DRFValidator)
        registry("func", "Function")(function_validator)

        # The submission object is not relevant for these validators, we use a dummy string instead
        res = registry.validate("django", "VALID", Submission())
        self.assertEqual(res.is_valid, True)
        self.assertEqual(res.messages, [])
        res = registry.validate("django", "INVALID", Submission())
        self.assertEqual(res.is_valid, False)
        self.assertEqual(res.messages, ["not VALID value"])

        res = registry.validate("drf", "VALID", Submission())
        self.assertEqual(res.is_valid, True)
        self.assertEqual(res.messages, [])
        res = registry.validate("drf", "INVALID", Submission())
        self.assertEqual(res.is_valid, False)
        self.assertEqual(res.messages, ["not VALID value"])

        res = registry.validate("func", "VALID", Submission())
        self.assertEqual(res.is_valid, True)
        self.assertEqual(res.messages, [])
        res = registry.validate("func", "INVALID", Submission())
        self.assertEqual(res.is_valid, False)
        self.assertEqual(res.messages, ["not VALID value"])

        res = registry.validate("NOT_REGISTERED", "VALID", Submission())
        self.assertEqual(res.is_valid, False)
        self.assertEqual(
            res.messages,
            [
                _("unknown validation plugin_id '{plugin_id}'").format(
                    plugin_id="NOT_REGISTERED"
                )
            ],
        )

    def test_validate_plugin_not_enabled(self):
        registry = Registry()
        registry("disabled", "Disabled")(DisabledValidator())

        res = registry.validate("disabled", "VALID", Submission())
        self.assertEqual(res.is_valid, False)
        self.assertEqual(
            res.messages,
            [_("plugin '{plugin_id}' not enabled").format(plugin_id="disabled")],
        )
