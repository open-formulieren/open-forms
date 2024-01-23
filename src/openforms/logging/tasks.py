from datetime import datetime
from typing import TypedDict

from openforms.celery import app
from openforms.forms.models import FormLogic
from openforms.typing import JSONObject, JSONValue


class EvaluatedRuleDict(TypedDict):
    rule_id: int
    triggered: bool
    action_log_data: dict[int, JSONValue]


@app.task(ignore_result=True)
def log_logic_evaluation(
    *,
    submission_id: int,
    timestamp: str,  # ISO-8601 timestamp
    evaluated_rules: list[EvaluatedRuleDict],
    initial_data: JSONObject,
    resolved_data: JSONObject,
):
    from openforms.submissions.logic.rules import EvaluatedRule
    from openforms.submissions.models import Submission

    from .logic import log_logic_evaluation as _log_logic_evaluation
    from .models import TimelineLogProxy

    # de-serialize the data bank into native python objects
    submission = Submission.objects.get(id=submission_id)
    rule_ids = [item["rule_id"] for item in evaluated_rules]
    rules = {
        rule.id: rule
        for rule in FormLogic.objects.filter(
            form_id=submission.form_id, id__in=rule_ids
        )
    }
    _evaluated_rules = [
        EvaluatedRule(
            rule=rules[item["rule_id"]],
            triggered=item["triggered"],
            action_log_data=item["action_log_data"],
        )
        for item in evaluated_rules
    ]

    log_entry = _log_logic_evaluation(
        submission, _evaluated_rules, initial_data, resolved_data
    )

    if not log_entry:
        return

    # overwrite the timestamp, since celery tasks run later than 'now'. This makes the
    # timestamp more accurate & matching with server time that ran the evaluation.
    _timestamp = datetime.fromisoformat(timestamp)
    TimelineLogProxy.objects.filter(pk=log_entry.pk).update(timestamp=_timestamp)
