from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class RenderModes(DjangoChoices):
    cli = ChoiceItem("cli", _("CLI"))
    pdf = ChoiceItem("pdf", _("PDF"))
    confirmation_email = ChoiceItem("confirmation_email", _("Confirmation email"))
    export = ChoiceItem("export", _("Submission export"))
