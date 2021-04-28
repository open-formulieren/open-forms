import logging
from typing import Optional

from openforms.submissions.models import Submission

logger = logging.getLogger(__name__)


def register_submission(submission: Submission) -> Optional[dict]:
    # figure out which registry and backend to use from the model field used
    form = submission.form
    backend = form.registration_backend
    registry = form._meta.get_field("registration_backend").registry

    if not backend:
        logger.info("Form %s has no registration plugin configured, aborting")
        return

    logger.debug("Looking up plugin with unique identifier '%s'", backend)
    plugin = registry[backend]

    logger.debug("De-serializing the plugin configuration options")
    options_serializer = plugin.configuration_options(
        data=form.registration_backend_options
    )
    options_serializer.is_valid(raise_exception=True)

    logger.debug("Invoking the '%r' plugin callback", plugin.callback)
    result = plugin.callback(submission, options_serializer.validated_data)

    if plugin.backend_feedback_serializer:
        logger.debug(
            "Serializing the callback result with '%r'",
            plugin.backend_feedback_serializer,
        )
        result_serializer = plugin.backend_feedback_serializer(instance=result)
        result_data = result_serializer.data
    else:
        logger.debug(
            "No result serializer specified, assuming raw result can be serialized as JSON"
        )
        result_data = result

    submission.backend_result = result_data
    submission.save(update_fields=["backend_result"])
