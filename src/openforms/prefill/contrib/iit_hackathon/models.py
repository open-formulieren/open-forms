from django.db import models
from django.utils.translation import gettext_lazy as _


class IITPrefillTestCase(models.Model):
    test = models.CharField(
        _("test name"),
        max_length=200,
        help_text=_("The name of the test in the test data set"),
    )
    bsn = models.CharField(
        _("test bsn"),
        max_length=50,
        help_text=_("BSN to connect to the prefill test data"),
    )

    class Meta:
        unique_together = (("test", "bsn"),)

    def __str__(self):
        return f"{self.bsn} -> {self.test}"
