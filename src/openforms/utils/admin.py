from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class SubmitActions(DjangoChoices):
    save = ChoiceItem("_save", _("Save"))
    add_another = ChoiceItem("_addanother", _("Save and add another"))
    edit_again = ChoiceItem("_continue", _("Save and continue editing"))
