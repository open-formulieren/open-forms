from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class AttachmentFormat(DjangoChoices):
    pdf = ChoiceItem("pdf", _("PDF"))
    csv = ChoiceItem("csv", _("CSV"))
    xlsx = ChoiceItem("xlsx", _("Excel"))
