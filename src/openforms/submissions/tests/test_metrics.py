import itertools
from collections.abc import Collection

from django.test import TestCase

from opentelemetry.metrics import CallbackOptions, Observation

from openforms.forms.tests.factories import FormFactory
from openforms.submissions.constants import Stages
from openforms.utils.tests.metrics_assert import MetricsAssertMixin

from ..metrics import count_submissions
from .factories import SubmissionFactory


def _group_observations_by(
    observations: Collection[Observation], attribute: str
) -> dict[str, int | float]:
    def _key_func(o: Observation) -> str:
        assert o.attributes is not None
        form_name = o.attributes[attribute]
        assert isinstance(form_name, str)
        return form_name

    grouped_by_attribute = itertools.groupby(
        sorted(observations, key=_key_func), key=_key_func
    )
    return {
        form_name: sum(o.value for o in _observations)
        for form_name, _observations in grouped_by_attribute
    }


class SubmissionCountMetricTests(MetricsAssertMixin, TestCase):
    def test_submission_counts_by_form_and_stage(self):
        form_1, form_2 = (
            FormFactory.create(name="Red"),
            FormFactory.create(name="Green"),
        )
        # stage: incomplete
        SubmissionFactory.create(form=form_1, completed=False)
        SubmissionFactory.create(form=form_1, completed=True)
        SubmissionFactory.create(form=form_1, completed_not_preregistered=True)
        SubmissionFactory.create(form=form_2, suspended=True)
        SubmissionFactory.create(form=form_2, registration_pending=True)
        SubmissionFactory.create(form=form_2, registration_in_progress=True)
        # stage: errored
        SubmissionFactory.create(form=form_1, registration_failed=True)
        SubmissionFactory.create(form=form_2, registration_failed=True)
        # stage: completed
        SubmissionFactory.create(form=form_1, registration_success=True)
        SubmissionFactory.create(form=form_2, registration_success=True)
        SubmissionFactory.create(form=form_2, registration_success=True)

        result = count_submissions(CallbackOptions())

        self.assertMarkedGlobal(result)
        assert all(o.attributes for o in result)

        with self.subTest(aggregation="total"):
            total = sum(observation.value for observation in result)

            self.assertEqual(total, 6 + 2 + 3)

        with self.subTest(aggregation="by form"):
            by_form = _group_observations_by(result, "form.name")

            self.assertEqual(
                by_form,
                {
                    "Red": 3 + 1 + 1,
                    "Green": 3 + 1 + 2,
                },
            )

        with self.subTest(aggregation="by stage"):
            by_stage = _group_observations_by(result, "type")

            self.assertEqual(
                by_stage,
                {
                    Stages.incomplete: 6,
                    Stages.errored: 2,
                    Stages.successfully_completed: 3,
                },
            )
