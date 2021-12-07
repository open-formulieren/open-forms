from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices

FORM_AUTH_SESSION_KEY = "form_auth"  # pending #957 rework

CO_SIGN_PARAMETER = "coSignSubmission"


class AuthAttribute(DjangoChoices):
    """
    core identifying attributes retrieved from the authentication plugins
    """

    bsn = ChoiceItem("bsn", _("BSN"))
    kvk = ChoiceItem("kvk", _("KvK number"))
    pseudo = ChoiceItem("pseudo", _("Pseudo ID"))
