from django.http import HttpResponseRedirect
from django.test import TestCase
from django.test.client import RequestFactory

from ...forms.tests.factories import FormStepFactory
from ...plugins.constants import UNIQUE_ID_MAX_LENGTH
from ..base import BasePlugin, PaymentInfo
from ..registry import Registry


class Plugin(BasePlugin):
    verbose_name = "some human readable label"
    return_method = "GET"
    webhook_method = "POST"

    def start_payment(self, request, payment, options):
        return PaymentInfo(type="get", url="http://testserver/foo")

    def handle_return(self, request, payment, options):
        return HttpResponseRedirect(payment.submission.form_url)

    def handle_webhook(self, request):
        return None


class RegistryTests(TestCase):
    def test_register_function(self):
        register = Registry()

        register("plugin1")(Plugin)

        plugin = register["plugin1"]

        self.assertIsInstance(plugin, Plugin)
        self.assertEqual(plugin.identifier, "plugin1")
        self.assertEqual(plugin.verbose_name, "some human readable label")
        self.assertEqual(plugin.get_label(), plugin.verbose_name)

    def test_duplicate_identifier(self):
        register = Registry()
        register("plugin")(Plugin)

        with self.assertRaisesMessage(
            ValueError,
            "The unique identifier 'plugin' is already present in the registry",
        ):
            register("plugin")(Plugin)

    def test_long_identifier(self):
        register = Registry()
        long_identifier = "x" * (UNIQUE_ID_MAX_LENGTH + 1)

        with self.assertRaisesMessage(
            ValueError,
            f"The unique identifier '{long_identifier}' is longer than {UNIQUE_ID_MAX_LENGTH} characters.",
        ):
            register(long_identifier)(Plugin)

    def test_get_choices(self):
        register = Registry()
        register("plugin1")(Plugin)

        choices = register.get_choices()
        self.assertEqual(choices, [("plugin1", "some human readable label")])

    def test_get_options(self):
        register = Registry()
        register("plugin1")(Plugin)

        factory = RequestFactory()
        request = factory.get("/xyz")
        step = FormStepFactory(
            form__slug="myform",
            form__payment_backend="plugin1",
            form__payment_backend_options={"foo": 1},
        )
        form = step.form
        self.assertEqual(form.payment_backend, "plugin1")

        options = register.get_options(request)
        self.assertEqual(len(options), 1)

        option = options[0]
        self.assertEqual(option.identifier, "plugin1")
        self.assertEqual(option.label, "some human readable label")
