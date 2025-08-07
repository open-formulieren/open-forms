from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PaymentsConfig(AppConfig):
    name = "openforms.payments"
    verbose_name = _("OpenForms Payments App")
    default_auto_field = "django.db.models.BigAutoField"
