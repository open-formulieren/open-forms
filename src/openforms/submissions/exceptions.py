from django.utils.translation import gettext_lazy as _

from openforms.api.exceptions import ServiceUnavailable, UnprocessableEntity


class FormDeactivated(UnprocessableEntity):
    default_detail = _("The form is deactivated.")
    default_code = "form-inactive"


class FormMaintenance(ServiceUnavailable):
    default_detail = _("The form is currently disabled for maintenance.")
    default_code = "form-maintenance"
