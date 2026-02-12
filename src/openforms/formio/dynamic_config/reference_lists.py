from django.utils.translation import gettext as _

from glom import glom
from requests.exceptions import RequestException
from zgw_consumers.client import build_client
from zgw_consumers.models import Service

from openforms.contrib.reference_lists.client import ReferenceListsClient
from openforms.logging import audit_logger
from openforms.submissions.models import Submission

from ..typing import Component


def fetch_options_from_reference_lists(
    component: Component, submission: Submission
) -> list[tuple[str, str]] | None:
    # TODO
    # We need to clean up the comoponent type and remove the ignore
    service_slug = glom(component, "openForms.service", default=None)
    code = glom(component, "openForms.code", default=None)
    audit_log = audit_logger.bind(form_id=submission.form.pk, component=component)
    if not service_slug:
        audit_log.warning(
            "form_configuration_error",
            error_message=_(
                "Cannot fetch from ReferenceLists API, because no `service` "
                "is configured."
            ),
        )
        return

    if not code:
        audit_log.warning(
            "form_configuration_error",
            error_message=_(
                "Cannot fetch from ReferenceLists API, because no `code` is configured."
            ),
        )
        return

    try:
        service = Service.objects.get(slug=service_slug)
    except Service.DoesNotExist:
        audit_log.warning(
            "form_configuration_error",
            error_message=_(
                "Cannot fetch from ReferenceLists API, service with {service_slug} "
                "does not exist."
            ).format(service_slug=service_slug),
        )
        return

    try:
        with build_client(service, client_factory=ReferenceListsClient) as client:
            # check if the table is valid (we don't want to show the possible valid
            # options of an invalid table)
            table = client.get_table(code)
            if table:
                if table.expires_on and table.is_expired:
                    return []

            items = client.get_items_for_table_cached(code)
    except RequestException as exc:
        audit_log.warning(
            "reference_lists_failure_response",
            error_message=_(
                "Exception occurred while fetching from ReferenceLists API: {exception}."
            ).format(exception=exc),
            exc_info=exc,
        )
        return
    else:
        if not items:
            audit_log.warning(
                "reference_lists_failure_response",
                error_message=_("No results found from ReferenceLists API."),
            )
            return

        return [
            (item.code, item.name)
            for item in items
            if not item.expires_on or not item.is_expired
        ]
