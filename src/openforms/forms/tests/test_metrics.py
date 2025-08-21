from django.test import TestCase

from opentelemetry.metrics import CallbackOptions

from openforms.utils.tests.metrics_assert import MetricsAssertMixin

from ..metrics import count_forms
from .factories import FormFactory


class FormCountMetricTests(MetricsAssertMixin, TestCase):
    def test_count_forms_by_type(self):
        # appointment forms
        FormFactory.create(is_appointment_form=True, deleted_=False)
        FormFactory.create(is_appointment_form=True, deleted_=True)
        # live forms
        FormFactory.create(deleted_=False, active=True, maintenance_mode=False)
        FormFactory.create(deleted_=False, active=True, maintenance_mode=True)
        FormFactory.create(deleted_=True, active=True, maintenance_mode=False)
        # with translations
        FormFactory.create(deleted_=False, active=True, translation_enabled=True)
        FormFactory.create(deleted_=False, active=False, translation_enabled=True)
        FormFactory.create(deleted_=True, translation_enabled=True)

        result = count_forms(CallbackOptions())

        counts_by_type = {
            observation.attributes["type"]: observation.value
            for observation in result
            if observation.attributes
        }
        self.assertEqual(
            counts_by_type,
            {
                "total": 1 + 2 + 2,  # 1 appointment, 2 live, 2 with translations
                "live": 1
                + 2
                + 1,  # 1 appointment, two active and not deleted, 1 active with translations
                "translation_enabled": 2,  # doesn't matter if they're active or not
                "is_appointment": 1,  # don't consider deleted forms
                "trash": 1 + 1 + 1,
            },
        )
        self.assertMarkedGlobal(result)
