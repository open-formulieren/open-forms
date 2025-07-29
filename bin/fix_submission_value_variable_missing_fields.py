#!/usr/bin/env python
#
# For GH-2324, we introduced a configuration field on the submission value variable.
# Existing variables need to be processed to fill this field, which is normally
# performed with a data migration. However, with a measured 'processing speed' of
# approximately 2500 variables/sec, and production environments with as much as 10
# million variables, this migration would take over an hour to complete. So we do it in
# a separate script instead.
from __future__ import annotations

import sys
from itertools import groupby
from pathlib import Path

import django

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def get_configuration(step):
    if step.form_step:
        return step.form_step.form_definition.configuration

    if not (history := step.form_step_history):
        return None

    return history["form_definition"]["fields"]["configuration"]


def add_configuration_to_existing_submission_value_variables() -> None:
    from openforms.formio.utils import iter_components
    from openforms.submissions.models import SubmissionStep, SubmissionValueVariable

    step_iterator = (
        SubmissionStep.objects.select_related(
            "form_step__form_definition", "submission"
        )
        .order_by("submission")
        .iterator()
    )
    # Note that we update the variables per submission because of performance reasons,
    # and to be able to run this script in batches. Only variables with an empty
    # configuration are selected, so running it again will not process the variables
    # multiple times.
    for _submission, step_group in groupby(step_iterator, key=lambda x: x.submission):
        variables_to_update = []

        for step in step_group:
            configuration = get_configuration(step)
            if not configuration:
                continue

            components_in_step = {
                component["key"]: component
                for component in iter_components(
                    configuration, recurse_into_editgrid=False
                )
            }

            # Note that a variable is unique by its key and submission
            variables_iterator = SubmissionValueVariable.objects.filter(
                configuration={}, key__in=components_in_step, submission=step.submission
            ).iterator()
            for variable in variables_iterator:
                if variable.key not in components_in_step:
                    # This can happen when the form definition still exists, but the
                    # field related to this submission variable was removed. We can't do
                    # anything in this case
                    continue

                variable.configuration = components_in_step[variable.key]
                variables_to_update.append(variable)

        SubmissionValueVariable.objects.bulk_update(
            variables_to_update, fields=["configuration"]
        )


def main(skip_setup=False, **kwargs):
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return add_configuration_to_existing_submission_value_variables()


if __name__ == "__main__":
    main()
