from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_better_admin_arrayfield.models.fields import ArrayField
from solo.models import SingletonModel


class ConfirmationEmailConfig(SingletonModel):
    email_template_url_allowlist = ArrayField(
        models.CharField(max_length=1000),
        verbose_name=_("Email template URL allowlist"),
        help_text=_(
            "A list of URLs (without https://www.) that will not be stripped "
            "from the content of confirmation emails"
        ),
        blank=True,
        default=list,
    )

    class Meta:
        verbose_name = _("Confirmation email configuration")
