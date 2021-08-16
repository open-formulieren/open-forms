from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class RemovalMethods(DjangoChoices):
    delete_permanently = ChoiceItem(
        "delete_permanently", _("Data will be permanently deleted")
    )
    make_anonymous = ChoiceItem(
        "make_anonymous", _("Data will be modified in a way to make it anonymous")
    )
