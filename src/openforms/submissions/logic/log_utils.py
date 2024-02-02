import contextlib
import logging
from typing import Iterator

from openforms.forms.models import FormLogic
from openforms.typing import JSONObject

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def log_errors(logic: JSONObject, rule: FormLogic) -> Iterator[None]:
    try:
        yield
    except Exception as error:
        logger.error(
            "Error in rule %s: evaluation of %s failed.", rule.pk, logic, exc_info=error
        )
