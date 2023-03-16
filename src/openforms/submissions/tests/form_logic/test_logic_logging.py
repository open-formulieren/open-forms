from django.test import TestCase, override_settings

from openforms.forms.constants import LogicActionTypes
from openforms.forms.tests.factories import FormLogicFactory, FormVariableFactory
from openforms.logging import logevent
from openforms.logging.models import TimelineLogProxy
from openforms.variables.constants import FormVariableDataTypes

from ...logic.datastructures import DataContainer
from ...logic.rules import iter_evaluate_rules
from ...models.submission_value_variable import SubmissionValueVariablesState
from ..factories import SubmissionFactory


@override_settings(LANGUAGE_CODE="nl")
class VariableActionLoggingTests(TestCase):
    def test_recorded_logdata(self):
        submission = SubmissionFactory.create()
        FormVariableFactory.create(
            form=submission.form,
            name="Number of large boxes",
            key="nLargeBoxes",
            data_type=FormVariableDataTypes.int,
        )
        FormVariableFactory.create(
            form=submission.form,
            name="Number of gigantic boxes",
            key="nGiganticBoxes",
            data_type=FormVariableDataTypes.int,
        )
        FormVariableFactory.create(
            form=submission.form,
            name="Total number of boxes",
            key="nTotalBoxes",
            data_type=FormVariableDataTypes.int,
        )
        variables_state = SubmissionValueVariablesState(submission=submission)
        initial_data = {"nLargeBoxes": 2, "nGiganticBoxes": 3}
        variables_state.set_values(initial_data)
        data_container = DataContainer(variables_state)

        evaluated_rules = []
        rule = FormLogicFactory.create(
            form=submission.form,
            json_logic_trigger=True,
            actions=[
                {
                    "variable": "nTotalBoxes",
                    "action": {
                        "type": LogicActionTypes.variable,
                        "value": {
                            "+": [{"var": "nLargeBoxes"}, {"var": "nGiganticBoxes"}]
                        },
                    },
                }
            ],
        )

        with self.subTest("Execute rule and record execution"):
            # evaluate and perform logging all in one go
            for _ in iter_evaluate_rules(
                [rule], data_container, on_rule_check=evaluated_rules.append
            ):
                pass

            # sanity check that our rule executed correctly
            self.assertEqual(data_container.data["nTotalBoxes"], 5)
            self.assertEqual(len(evaluated_rules), 1)

        with self.subTest("Store log records suitable for display"):
            with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
                logevent.submission_logic_evaluated(
                    submission,
                    evaluated_rules,
                    initial_data,
                    data_container.data,
                )

            log_entries = TimelineLogProxy.objects.filter(
                template="logging/events/submission_logic_evaluated.txt"
            )

            self.assertEqual(log_entries.count(), 1)
            log_data = log_entries.get().extra_data

            self.assertEqual(
                log_data["input_data"],
                {
                    "nLargeBoxes": {
                        "key": "nLargeBoxes",
                        "value": 2,
                        "step_name": "",
                        "label": "Number of large boxes",
                    },
                    "nGiganticBoxes": {
                        "key": "nGiganticBoxes",
                        "value": 3,
                        "step_name": "",
                        "label": "Number of gigantic boxes",
                    },
                },
            )
            _evaluated_rules = log_data["evaluated_rules"]
            self.assertEqual(len(_evaluated_rules), 1)
            logged_rule = _evaluated_rules[0]
            self.assertEqual(logged_rule["raw_logic_expression"], True)
            self.assertEqual(logged_rule["readable_rule"], "true")
            self.assertEqual(
                logged_rule["targeted_components"],
                [
                    {
                        "key": "nTotalBoxes",
                        "type_display": "Stel de waarde van een variabele in",
                        "value": "{{nLargeBoxes}} + {{nGiganticBoxes}}",
                        "raw_logic_expression": {
                            "+": [{"var": "nLargeBoxes"}, {"var": "nGiganticBoxes"}]
                        },
                    }
                ],
            )
