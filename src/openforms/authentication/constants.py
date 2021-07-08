from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class AuthAttribute(DjangoChoices):
    """
    core identifying attributes retrieved from the authentication plugins
    """

    bsn = ChoiceItem("bsn", _("citizen service number"))
    kvk = ChoiceItem("kvk", _("chamber of commerce number"))
