from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class RemovalMethods(DjangoChoices):
    delete_permanently = ChoiceItem(
        "delete_permanently", _("Submissions will be deleted")
    )
    make_anonymous = ChoiceItem(
        "make_anonymous", _("Sensitive data within the submissions will be deleted")
    )
