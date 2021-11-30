from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices

FORM_AUTH_SESSION_KEY = "form_auth"  # pending #957 rework


class AuthAttribute(DjangoChoices):
    """
    core identifying attributes retrieved from the authentication plugins
    """

    bsn = ChoiceItem("bsn", _("BSN"))
    acting_bsn = ChoiceItem("acting_bsn", _("BSN van gemachtigde"))
    kvk = ChoiceItem("kvk", _("KvK number"))
    pseudo = ChoiceItem("pseudo", _("Pseudo ID"))
