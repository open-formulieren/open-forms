from django.test import TestCase

from opentelemetry.metrics import CallbackOptions

from openforms.utils.tests.metrics_assert import MetricsAssertMixin

from ..registry import BaseRegistry, record_plugin_usage


class PluginRegistryMetricTests(MetricsAssertMixin, TestCase):
    def test_report_zero_counts_for_empty_database(self):
        result = list(record_plugin_usage(CallbackOptions()))

        self.assertGreater(len(result), 0)
        self.assertMarkedGlobal(result)

        with self.subTest("modules reported"):
            modules = {
                observation.attributes["plugin.module"]
                for observation in result
                if observation.attributes
            }

            self.assertEqual(
                modules,
                {
                    "appointments",
                    "authentication",
                    "dmn",
                    "payments",
                    "prefill",
                    "registrations",
                    "validations",
                },
            )

        for observation in result:
            assert observation.attributes
            with self.subTest(
                "zero counts reported",
                module=observation.attributes["plugin.module"],
                plugin=observation.attributes["plugin.identifier"],
            ):
                self.assertEqual(observation.value, 0)

    def test_base_report_plugin_usage_is_empty(self):
        register = BaseRegistry()

        result = register.report_plugin_usage()

        self.assertEqual(len(list(result)), 0)

    def test_cannot_set_another_register_instance_as_metrics_reporter(self):
        class BadRegistry(BaseRegistry):
            module = "appointments"

        bad_register = BadRegistry()

        with self.assertRaises(ValueError):
            bad_register.set_as_metric_reporter()
