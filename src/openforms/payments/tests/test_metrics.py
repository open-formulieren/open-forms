from django.http import HttpResponseRedirect
from django.test import TestCase

from openforms.forms.tests.factories import FormFactory

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


register = Registry()
register("test1")(Plugin)
register("test2")(Plugin)


class ReportPluginUsageTests(TestCase):
    def test_report_counts_from_live_forms(self):
        FormFactory.create_batch(2, payment_backend="test1")
        FormFactory.create(payment_backend="test2", active=False)
        FormFactory.create(payment_backend="test2", active=True, deleted_=True)

        result = {
            plugin.identifier: count for plugin, count in register.report_plugin_usage()
        }

        self.assertEqual(result, {"test1": 2, "test2": 0})
