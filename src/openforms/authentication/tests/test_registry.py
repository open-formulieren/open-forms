from django.test import TestCase
from django.test.client import RequestFactory

from rest_framework.reverse import reverse

from ...forms.tests.factories import FormStepFactory
from ..base import BasePlugin
from ..registry import Registry, register as auth_register


class Plugin(BasePlugin):
    verbose_name = "some human readable label"


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

    def test_get_choices(self):
        register = Registry()
        register("plugin1")(Plugin)

        choices = register.get_choices()
        self.assertEqual(choices, [("plugin1", "some human readable label")])

    def test_get_options(self):
        register = Registry()

        register("plugin1")(Plugin)

        plugin = register["plugin1"]
        factory = RequestFactory()
        request = factory.get("/xyz")
        step = FormStepFactory(
            form__slug="myform",
            form__authentication_backends=["plugin1"],
            form_definition__login_required=True,
        )
        form = step.form
        self.assertEqual(form.authentication_backends, ["plugin1"])

        options = register.get_options(request, form)
        self.assertEqual(len(options), 1)

        option = options[0]
        self.assertEqual(option.identifier, "plugin1")
        self.assertEqual(option.label, "some human readable label")
        self.assertEqual(option.url, plugin.get_start_url(request, form))

    def test_urls(self):
        register = auth_register  # Registry()
        register("plugin1")(Plugin)
        plugin = register["plugin1"]

        step = FormStepFactory(
            form__slug="myform",
            form__authentication_backends=["plugin1"],
            form_definition__login_required=True,
        )
        form = step.form

        # we need an arbitrary request
        factory = RequestFactory()
        request = factory.get("/foo")

        url = plugin.get_start_url(request, form)
        self.assertRegex(url, r"^http://")
        self.assertEqual(
            url,
            reverse(
                "authentication:start",
                request=request,
                kwargs={"slug": "myform", "plugin_id": "plugin1"},
            ),
        )

        url = plugin.get_return_url(request, form)
        self.assertRegex(url, r"^http://")
        self.assertEqual(
            url,
            reverse(
                "authentication:return",
                request=request,
                kwargs={"slug": "myform", "plugin_id": "plugin1"},
            ),
        )
