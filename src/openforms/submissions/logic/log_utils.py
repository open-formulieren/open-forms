import contextlib
from collections.abc import Iterator

import structlog

from openforms.forms.models import FormLogic
from openforms.typing import JSONObject

logger = structlog.stdlib.get_logger(__name__)


@contextlib.contextmanager
def log_errors(logic: JSONObject, rule: FormLogic) -> Iterator[None]:
    log = logger.bind(rule_id=rule.pk)
    try:
        yield
    except Exception as error:
        log.error(
            "submissions.logic_rule_evaluation_failure", logic=logic, exc_info=error
        )
