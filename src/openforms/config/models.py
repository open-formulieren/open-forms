from django.db import models
from django.utils.encoding import force_str
from django.utils.translation import ugettext_lazy as _

from django_better_admin_arrayfield.models.fields import ArrayField
from solo.models import SingletonModel


class GlobalConfiguration(SingletonModel):
    email_template_netloc_allowlist = ArrayField(
        models.CharField(max_length=1000),
        verbose_name=_("Toegestane domeinen in e-mails."),
        help_text=_(
            "Geef een lijst van toegelaten domeinen op (zonder 'https://www.'). "
            "Hyperlinks in (bevestigings)e-mails worden verwijderd, tenzij het domein "
            "hier opgegeven is."
        ),
        blank=True,
        default=list,
    )

    class Meta:
        verbose_name = _("Global configuration")

    def __str__(self):
        return force_str(self._meta.verbose_name)
