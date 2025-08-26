from django.test import TestCase

from opentelemetry.metrics import CallbackOptions

from openforms.utils.tests.metrics_assert import MetricsAssertMixin

from ..metrics import count_component_usage, count_forms
from .factories import FormDefinitionFactory, FormFactory, FormStepFactory


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


class FormComponentCountMetricTests(MetricsAssertMixin, TestCase):
    def test_ignores_forms_that_are_not_live(self):
        # deactivated_form
        FormFactory.create(generate_minimal_setup=True, active=False, deleted_=False)
        # deleted_form
        FormFactory.create(generate_minimal_setup=True, active=True, deleted_=True)

        result = count_component_usage(CallbackOptions())

        self.assertEqual(len(result), 0)

    def test_counts_components_used_per_form(self):
        fd1 = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {"type": "textfield", "key": "component1"},
                    {
                        "type": "fieldset",
                        "key": "component2",
                        "components": [
                            {"type": "textfield", "key": "component3"},
                            {"type": "select", "key": "component4"},
                        ],
                    },
                ]
            }
        )
        fd2 = FormDefinitionFactory.create(
            configuration={
                "components": [
                    {"type": "number", "key": "component5"},
                ]
            }
        )
        form_1, form_2 = FormFactory.create_batch(
            2, active=True, deleted_=False, is_appointment=False
        )
        FormStepFactory.create(form=form_1, form_definition=fd1)
        FormStepFactory.create(form=form_1, form_definition=fd2)
        FormStepFactory.create(form=form_2, form_definition=fd2)

        # one query for the forms, one prefetch query for the form steps
        with self.assertNumQueries(2):
            result = count_component_usage(CallbackOptions())

        self.assertMarkedGlobal(result)

        with self.subTest("counts by form"):
            counts_by_form = self._group_observations_by(result, "form.name")

            expected = {
                form_1.name: 4 + 1,  # components of fd1 and fd2
                form_2.name: 1,  # only the component of fd2
            }
            self.assertEqual(counts_by_form, expected)

        with self.subTest("counts by type"):
            counts_by_type = self._group_observations_by(result, "type")

            expected = {
                "textfield": 2,  # fd1 is used once
                "fieldset": 1,  # fd1 is used once
                "select": 1,  # fd1 is used once
                "number": 1 + 1,  # fd2 is used twice
            }
            self.assertEqual(counts_by_type, expected)
