from typing import Any, Dict

from .models import SubmissionStep


def evaluate_form_logic(step: SubmissionStep, data: Dict[str, Any]) -> None:
    """
    Process all the form logic rules and mutate the step configuration if required.
    """
    # grab the configuration that can be **mutated**
    configuration = step.form_step.form_definition.configuration

    # TODO: actual evaluations
    step._can_submit = False
    for component in configuration["components"]:
        if label := component.get("label"):
            component["label"] = f"{label} (updated by logic check)"
