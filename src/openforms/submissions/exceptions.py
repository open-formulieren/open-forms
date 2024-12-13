from django.utils.translation import gettext_lazy as _

from openforms.api.exceptions import ServiceUnavailable, UnprocessableEntity


class FormDeactivated(UnprocessableEntity):
    default_detail = _("The form is deactivated.")
    default_code = "form-inactive"


class FormMaintenance(ServiceUnavailable):
    default_detail = _("The form is currently disabled for maintenance.")
    default_code = "form-maintenance"


class FormMaximumSubmissions(ServiceUnavailable):
    default_detail = _("The form has reached the maximum number of submissions.")
    default_code = "form-submission-limit-reached"
