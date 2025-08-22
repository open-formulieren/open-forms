from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase
from django.utils.translation import gettext as _

from rest_framework.exceptions import ValidationError as DRFValidationError

from openforms.submissions.models import Submission

from ..base import BasePlugin
from ..registry import Registry


class DjangoValidator(BasePlugin[str]):
    for_components = ("textfield",)
    verbose_name = "Django Test Validator"

    def __call__(self, value, submission):
        if value != "VALID":
            raise DjangoValidationError("not VALID value")


class DRFValidator(BasePlugin[str]):
    for_components = ("phoneNumber",)
    verbose_name = "DRF Test Validator"

    def __call__(self, value, submission):
        if value != "VALID":
            raise DRFValidationError("not VALID value")


class DisabledValidator(BasePlugin[str]):
    for_components = ("textfield",)

    def __call__(self, value, submission):
        if value != "VALID":
            raise DRFValidationError("not VALID value")

    @property
    def is_enabled(self) -> bool:
        return False


class RegistryTest(TestCase):
    def test_register_function(self):
        register = Registry()
        register("plugin")(DjangoValidator)
        plugin = register["plugin"]
        self.assertIsInstance(plugin, DjangoValidator)

    def test_duplicate_identifier(self):
        register = Registry()
        register("plugin")(DjangoValidator)

        with self.assertRaisesMessage(
            ValueError,
            "The unique identifier 'plugin' is already present in the registry.",
        ):
            register("plugin")(DjangoValidator)

    def test_validate(self):
        registry = Registry()
        registry("django")(DjangoValidator)
        registry("drf")(DRFValidator)

        # The submission object is not relevant for these validators, we use a dummy object instead
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
        registry("disabled")(DisabledValidator)

        res = registry.validate("disabled", "VALID", Submission())
        self.assertFalse(res.is_valid)
        self.assertEqual(
            res.messages,
            [_("plugin '{plugin_id}' not enabled").format(plugin_id="disabled")],
        )
