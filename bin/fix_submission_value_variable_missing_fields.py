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

from tqdm import tqdm

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def get_configuration(step):
    if step.form_step:
        return step.form_step.form_definition.configuration

    if not (history := step.form_step_history):
        return None

    return history["form_definition"]["fields"]["configuration"]


def add_missing_fields_to_existing_submission_value_variables() -> None:
    from openforms.formio.utils import (
        get_component_data_subtype,
        get_component_datatype,
        iter_components,
    )
    from openforms.submissions.models import SubmissionStep, SubmissionValueVariable
    from openforms.variables.constants import FormVariableSources

    queryset = SubmissionStep.objects.select_related(
        "form_step__form_definition", "submission", "submission__form"
    ).order_by("submission")

    # Note that we update the variables per submission because of performance reasons,
    # and to be able to run this script in batches. Only variables with an empty
    # configuration are selected, so running it again will not process the variables
    # multiple times.
    for submission, step_group in tqdm(
        groupby(queryset.iterator(), key=lambda x: x.submission),
        desc="Submission steps processed",
        total=queryset.count(),
        dynamic_ncols=True,
        mininterval=0.5,
        disable=None,
        unit="step",
    ):
        variables_to_update = []

        components_in_submission = set()
        # Process component submission variables
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
            components_in_submission.update(components_in_step.keys())

            # Note that a variable is unique by its key and submission
            variables_iterator = SubmissionValueVariable.objects.filter(
                configuration={},
                data_type="",
                data_subtype="",
                key__in=components_in_step,
                submission=step.submission,
            ).iterator()
            for variable in variables_iterator:
                component = components_in_step[variable.key]

                variable.configuration = component
                variable.data_type = get_component_datatype(component)
                variable.data_subtype = get_component_data_subtype(component)
                variables_to_update.append(variable)

        # Process non-component submission variables
        form_variables = submission.form.formvariable_set.exclude(
            source=FormVariableSources.component
        )

        variables_iterator = (
            SubmissionValueVariable.objects.filter(
                data_type="", data_subtype="", submission=submission
            )
            .exclude(key__in=components_in_submission)
            .iterator()
        )
        for variable in variables_iterator:
            form_var = form_variables.filter(key=variable.key).first()
            if not form_var:
                # Cannot do anything if it doesn't exist anymore
                continue

            variable.data_type = form_var.data_type
            variable.data_subtype = form_var.data_subtype
            variables_to_update.append(variable)

        SubmissionValueVariable.objects.bulk_update(
            variables_to_update, fields=["configuration", "data_type", "data_subtype"]
        )


def main(skip_setup=False, **kwargs):
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    add_missing_fields_to_existing_submission_value_variables()


if __name__ == "__main__":
    main()
