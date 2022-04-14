from glom import glom

from openforms.dmn.models import DMNEvaluationResult
from openforms.formio.utils import iter_components


def apply_dmn_prefill(config: dict, submission):
    evaluation_results = {
        evaluation.component: evaluation
        for evaluation in DMNEvaluationResult.objects.filter(submission=submission)
    }
    if not evaluation_results:
        return

    for component in iter_components(config, recursive=True):
        dmn_prefill_config = glom(component, "prefill.fromDmn", default=None)
        if dmn_prefill_config is None:
            continue

        component_key = dmn_prefill_config.get("component")
        data_path = dmn_prefill_config.get("dataPath")
        if (
            not component_key
            or not data_path
            or component_key not in evaluation_results
        ):
            continue

        result = evaluation_results[component_key]

        extracted = glom(result.result, data_path, default=None)
        if extracted is None:
            continue

        # set the default value
        component["defaultValue"] = extracted
