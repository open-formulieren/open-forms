from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class TimelineLogTags(DjangoChoices):
    AVG = ChoiceItem("avg", _("AVG"))
    hijack = ChoiceItem("hijack", _("Hijack"))
