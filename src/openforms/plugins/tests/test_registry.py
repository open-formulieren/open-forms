from unittest.mock import patch

from django.db import OperationalError
from django.test import TestCase

from openforms.config.models import GlobalConfiguration

from ..plugin import AbstractBasePlugin
from ..registry import BaseRegistry


class Registry1(BaseRegistry):
    module = "test"


register1 = Registry1()


@register1("plugin1")
class TestPlugin1(AbstractBasePlugin):
    verbose_name = "Test1"


@register1("plugin2")
class TestPlugin2(AbstractBasePlugin):
    verbose_name = "Test2"


class Registry2(BaseRegistry):
    module = "test2"


register2 = Registry2()


@register2("plugin2")
class TestPluginDifferentNamespace(AbstractBasePlugin):
    verbose_name = "Test2"


class RegistryTestCase(TestCase):
    def test_registry_iter_enabled_plugins(self):
        config = GlobalConfiguration.get_solo()
        config.plugin_configuration = {
            "test": {
                "plugin1": {"enabled": False},
                "plugin2": {"enabled": True},
            },
        }
        config.save()

        plugins = [x for x in register1.iter_enabled_plugins()]

        self.assertEqual(len(plugins), 1)
        self.assertEqual(plugins[0].identifier, "plugin2")

    def test_registry_iter_enabled_plugins_default_enabled(self):
        config = GlobalConfiguration.get_solo()
        config.plugin_configuration = {
            "test": {
                "plugin1": {"enabled": True},
            },
        }
        config.save()

        plugins = [x for x in register1.iter_enabled_plugins()]

        self.assertEqual(len(plugins), 2)
        self.assertEqual(plugins[0].identifier, "plugin1")
        self.assertEqual(plugins[1].identifier, "plugin2")

    def test_registry_iter_enabled_plugins_no_config_default_enabled(self):
        config = GlobalConfiguration.get_solo()
        config.plugin_configuration = {}
        config.save()

        plugins = [x for x in register1.iter_enabled_plugins()]

        self.assertEqual(len(plugins), 2)
        self.assertEqual(plugins[0].identifier, "plugin1")
        self.assertEqual(plugins[1].identifier, "plugin2")

    def test_registry_iter_enabled_plugins_multiple_namespaces(self):
        config = GlobalConfiguration.get_solo()
        config.plugin_configuration = {
            "test": {
                "plugin1": {"enabled": True},
                "plugin2": {"enabled": True},
            },
            "test2": {
                "plugin1": {"enabled": False},
            },
        }
        config.save()

        plugins_namespace1 = [x for x in register1.iter_enabled_plugins()]

        self.assertEqual(len(plugins_namespace1), 2)
        self.assertEqual(plugins_namespace1[0].identifier, "plugin1")
        self.assertEqual(plugins_namespace1[0].registry, register1)
        self.assertEqual(plugins_namespace1[1].identifier, "plugin2")
        self.assertEqual(plugins_namespace1[1].registry, register1)

        plugins_namespace2 = [x for x in register2.iter_enabled_plugins()]

        self.assertEqual(len(plugins_namespace2), 1)
        self.assertEqual(plugins_namespace2[0].identifier, "plugin2")
        self.assertEqual(plugins_namespace2[0].registry, register2)

    def test_registry_iter_enabled_plugins_no_database_enable_all(self):
        config = GlobalConfiguration.get_solo()
        config.plugin_configuration = {
            "test": {
                "plugin1": {"enabled": False},
                "plugin2": {"enabled": False},
            },
        }
        config.save()

        # When the OAS is generated, the database is not used
        with patch("openforms.config.models.GlobalConfiguration.get_solo") as m:
            m.side_effect = OperationalError()
            plugins = [x for x in register1.iter_enabled_plugins()]

        self.assertEqual(len(plugins), 2)
        self.assertEqual(plugins[0].identifier, "plugin1")
        self.assertEqual(plugins[1].identifier, "plugin2")
