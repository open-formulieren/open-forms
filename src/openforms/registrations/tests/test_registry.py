from django.test import SimpleTestCase

from rest_framework import serializers

from ..base import BasePlugin
from ..registry import Registry


class OptionsSerializer(serializers.Serializer):
    pass


class Plugin(BasePlugin):
    verbose_name = "some human readable label"
    configuration_options = OptionsSerializer


class NoConfigPlugin(BasePlugin):
    verbose_name = "some human readable label"
    configuration_options = None


class RegistryTests(SimpleTestCase):
    def test_register_function(self):
        register = Registry()

        register("plugin1")(Plugin)

        plugin = register["plugin1"]

        self.assertIsInstance(plugin, Plugin)
        self.assertEqual(plugin.identifier, "plugin1")
        self.assertEqual(plugin.verbose_name, "some human readable label")

    def test_duplicate_identifier(self):
        register = Registry()
        register("plugin")(Plugin)

        with self.assertRaisesMessage(
            ValueError,
            "The unique identifier 'plugin' is already present in the registry",
        ):
            register("plugin")(Plugin)

    def test_missing_configuration_options(self):
        register = Registry()

        with self.assertRaisesMessage(
            ValueError,
            "Please specify 'configuration_options' attribute for plugin class.",
        ):
            register("plugin")(NoConfigPlugin)
