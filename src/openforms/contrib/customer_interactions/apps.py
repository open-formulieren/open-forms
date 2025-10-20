from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CustomerInteractionsApp(AppConfig):
    name = "openforms.contrib.customer_interactions"
    label = "customer_interactions"
    verbose_name = _("Customer interactions")
