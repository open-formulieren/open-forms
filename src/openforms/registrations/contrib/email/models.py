from django.db import models
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel


class EmailConfig(SingletonModel):
    """
    Global configuration and defaults for the email registration backend.
    """

    attach_files_to_email = models.BooleanField(
        _("attach files to email"),
        default=False,
        help_text=_(
            "Enable to attach file uploads to the registration email. Note that this "
            "is the global default which may be overridden per form. Form designers "
            "should take special care to ensure that the total file upload sizes do "
            "not exceed the email size limit."
        ),
    )

    class Meta:
        verbose_name = _("Email registration configuration")

    def __str__(self):
        return force_str(self._meta.verbose_name)

    def apply_defaults_to(self, options: dict):
        # key may be present and have the value None, or may be absent -> .get also returns None
        current_val = options.get("attach_files_to_email")
        if current_val is None:
            options["attach_files_to_email"] = self.attach_files_to_email
