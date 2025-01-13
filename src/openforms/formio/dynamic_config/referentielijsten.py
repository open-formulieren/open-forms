from django.utils.translation import gettext as _

from glom import glom
from requests.exceptions import RequestException
from zgw_consumers.client import build_client
from zgw_consumers.models import Service

from openforms.contrib.referentielijsten.client import ReferentielijstenClient
from openforms.logging import logevent
from openforms.submissions.models import Submission

from ..typing import Component


def fetch_options_from_referentielijsten(
    component: Component, submission: Submission
) -> list[tuple[str, str]] | None:
    service_slug = glom(component, "openForms.service", default=None)
    code = glom(component, "openForms.code", default=None)
    if not service_slug:
        logevent.form_configuration_error(
            submission.form,
            component,
            _(
                "Cannot fetch from Referentielijsten API, because no `service` is configured."
            ),
        )
        return

    if not code:
        logevent.form_configuration_error(
            submission.form,
            component,
            _(
                "Cannot fetch from Referentielijsten API, because no `code` is configured."
            ),
        )
        return

    try:
        service = Service.objects.get(slug=service_slug)
    except Service.DoesNotExist:
        logevent.form_configuration_error(
            submission.form,
            component,
            _(
                "Cannot fetch from Referentielijsten API, service with {service_slug} does not exist."
            ).format(service_slug=service_slug),
        )
        return

    try:
        with build_client(service, client_factory=ReferentielijstenClient) as client:
            result = client.get_items_for_tabel_cached(code)
    except RequestException as e:
        logevent.referentielijsten_failure_response(
            submission.form,
            component,
            _(
                "Exception occurred while fetching from Referentielijsten API: {exception}."
            ).format(exception=e),
        )
        return
    else:
        if not result:
            logevent.referentielijsten_failure_response(
                submission.form,
                component,
                _("No results found from Referentielijsten API."),
            )
        return [[item["code"], item["naam"]] for item in result]
