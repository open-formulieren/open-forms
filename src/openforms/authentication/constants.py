from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class AuthAttribute(DjangoChoices):
    bsn = ChoiceItem("bsn", _("citizen service number"))
    kvk = ChoiceItem("kvk", _("chamber of commerce number"))

    # TODO implement these fields on Submission model
    # nnpid = ChoiceItem("nnpid", _("non-natural person number"))
    rsin = ChoiceItem("rsin", _("RSIN"))
    branchNumber = ChoiceItem(
        "branchNumber", _("chamber of commerce number branch number")
    )
